import { useCallback, useEffect, useRef, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { apiMessage, EmptyState, Meter, Notice, PageHeader, SectionHeading, Severity, severityLabels, severityTones, Status, TextLink } from '../common/Workspace';

interface ScanResult {
  status: string;
  completed_at: string | null;
  passed_checks: number;
  failed_checks: number;
}

interface Finding {
  id: string;
  title: string;
  severity: string;
  cvss_score: number | null;
  resource_type: string;
  resource_id: string;
  status: string;
}

interface Summary {
  total_open_vulnerabilities: number;
  average_cvss_score: number;
  severity_distribution: Record<string, number>;
  resource_distribution: Record<string, number>;
}

interface Snapshot {
  scans: ScanResult[];
  findings: Finding[];
  summary: Summary | null;
  frameworks: Record<string, number> | null;
  updated: Date;
}

interface TrendPoint { date: string | null; score: number; sample: boolean }
const severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const shortDate = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' });
const fullDate = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });
const shortTime = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' });
const checksIn = (scan: ScanResult) => (scan.passed_checks || 0) + (scan.failed_checks || 0);

function ComplianceTrend({ points }: { points: TrendPoint[] }) {
  if (points.length < 2) return <EmptyState title="Two finished scans are needed"><p>Each scan must have evaluated checks.</p></EmptyState>;
  const x = (index: number) => 1 + index * 98 / (points.length - 1);
  const y = (score: number) => 100 - score;
  const dateLabel = (point: TrendPoint) => point.date ? shortDate.format(new Date(point.date)) : 'Date unavailable';

  return <>
    <div className="trend" aria-hidden="true">
      <div className="trend-scale"><span>100%</span><span>50%</span><span>0%</span></div>
      <div className="trend-plot">
        <div className="trend-chart">
          <div className="trend-rules"><i /><i /><i /></div>
          <svg viewBox="0 0 100 100" preserveAspectRatio="none">
            <polyline points={points.map(({ score }, index) => `${x(index)},${y(score)}`).join(' ')}
              fill="none" stroke="currentColor" strokeWidth="2" vectorEffect="non-scaling-stroke" />
          </svg>
          {points.map(({ score }, index) => <span key={index} className="trend-point" style={{ left: `${x(index)}%`, top: `${y(score)}%` }} />)}
        </div>
      </div>
      <div className="trend-dates"><span>{dateLabel(points[0])}</span><span>{dateLabel(points[points.length - 1])}</span></div>
    </div>
    <details className="chart-values">
      <summary>Scan values</summary>
      <ul>{points.map((point, index) => <li key={index} className="line-row">
        <span>{point.date ? fullDate.format(new Date(point.date)) : 'Date unavailable'}{point.sample && ' · Sample'}</span>
        <strong className="number">{point.score}%</strong>
      </li>)}</ul>
    </details>
  </>;
}

export function Dashboard() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const currentRequest = useRef<AbortController | null>(null);

  const refresh = useCallback(async (background = false) => {
    if (currentRequest.current) return;
    const request = new AbortController();
    currentRequest.current = request;
    const { signal } = request;
    if (!background) setLoading(true);
    setError('');
    try {
      const [scans, findings, summary, frameworks] = await Promise.allSettled([
        api.get<ScanResult[]>('/scans', { signal }),
        api.get<Finding[]>('/vulnerabilities', { signal }),
        api.get<Summary>('/analytics/summary', { signal }),
        api.get<Record<string, number>>('/compliance/summary', { signal }),
      ]);
      if (signal?.aborted) return;
      if (scans.status === 'rejected') throw scans.reason;
      if (findings.status === 'rejected') throw findings.reason;
      setSnapshot({
        scans: scans.value.data,
        findings: findings.value.data,
        summary: summary.status === 'fulfilled' ? summary.value.data : null,
        frameworks: frameworks.status === 'fulfilled' ? frameworks.value.data : null,
        updated: new Date(),
      });
    } catch (error) {
      if (!signal?.aborted) setError(apiMessage(error, 'Could not load cloud posture. Try refreshing.'));
    } finally {
      if (currentRequest.current === request) {
        currentRequest.current = null;
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void refresh();
    const poll = window.setInterval(() => {
      if (document.visibilityState === 'visible') void refresh(true);
    }, 30_000);
    return () => {
      window.clearInterval(poll);
      currentRequest.current?.abort();
      currentRequest.current = null;
    };
  }, [refresh]);

  const header = <PageHeader title="Cloud posture" description="Evaluated checks and findings across your cloud scans."
    action={<>
      {snapshot && <span className="refresh-status"><Status>{error ? 'Refresh failed' : 'Auto-refresh'}</Status><time className="meta" dateTime={snapshot.updated.toISOString()}>Updated {shortTime.format(snapshot.updated)}</time></span>}
      <button className="button" type="button" onClick={() => void refresh()} disabled={loading}><RefreshCw size={16} aria-hidden="true" />{loading ? 'Refreshing…' : 'Refresh'}</button>
    </>} />;

  if (!snapshot) return <div className="page">{header}{loading ? <LoadingSpinner label="Loading cloud posture…" /> : <Notice tone="error">{error}</Notice>}</div>;

  const { scans, findings, summary, frameworks } = snapshot;
  const evaluated = scans.filter(scan => ['COMPLETED', 'DEMO_COMPLETED'].includes(scan.status) && checksIn(scan) > 0)
    .sort((a, b) => (a.completed_at ? Date.parse(a.completed_at) : 0) - (b.completed_at ? Date.parse(b.completed_at) : 0));
  const passed = evaluated.reduce((total, scan) => total + (scan.passed_checks || 0), 0);
  const checks = evaluated.reduce((total, scan) => total + checksIn(scan), 0);
  const rate = checks ? Math.round(passed / checks * 100) : null;
  const activeFindings = findings.filter(finding => finding.status === 'OPEN');
  const count = (severity: string) => summary
    ? summary.severity_distribution?.[severity] ?? 0
    : activeFindings.filter(finding => finding.severity === severity).length;
  const maxSeverity = Math.max(1, ...severities.map(count));
  const priority = findings.filter(finding => ['OPEN', 'IN_PROGRESS'].includes(finding.status) && (finding.severity === 'CRITICAL' || finding.severity === 'HIGH'))
    .sort((a, b) => (b.cvss_score ?? 0) - (a.cvss_score ?? 0)).slice(0, 5);
  const resources = Object.entries(summary?.resource_distribution ?? {}).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const frameworkEntries = Object.entries(frameworks ?? {}).sort((a, b) => a[1] - b[1]);
  const points = evaluated.map(scan => ({ date: scan.completed_at, score: Math.round((scan.passed_checks || 0) / checksIn(scan) * 100), sample: scan.status === 'DEMO_COMPLETED' }));

  return <div className="page dashboard">
    {header}
    {error && <Notice tone="error">Showing data from the last successful refresh. {error}</Notice>}
    <div className="stack-lg">
      <dl className="posture-totals" aria-label="Scan totals">
        <div><dt>Scan runs</dt><dd className="number">{scans.length}</dd></div>
        <div><dt>Open findings</dt><dd className="number">{summary?.total_open_vulnerabilities ?? activeFindings.length}</dd></div>
        <div><dt>Critical open</dt><dd className="number" data-tone="error">{count('CRITICAL')}</dd></div>
        <div><dt>Scans running</dt><dd className="number">{scans.filter(scan => ['PENDING', 'RUNNING'].includes(scan.status)).length}</dd></div>
      </dl>
      <div className="split dashboard-top">
        <section className="ledger posture-block" aria-labelledby="pass-rate-heading">
          <SectionHeading title="Compliance over time" id="pass-rate-heading" action={<TextLink to="/policies">Policy checks</TextLink>} />
          <div className="posture-inner">
            <div className="posture-reading">
              <div><p className="posture-label">Check pass rate</p>
                <p className="posture-number number">{rate === null ? '—' : <>{rate}<span>%</span></>}</p></div>
              <div><p className="muted">{checks ? `${passed} of ${checks} checks passed across finished scans.` : 'No checks have been evaluated yet.'}</p>
              {points.some(point => point.sample) && <p className="meta">Includes checks from sample scans.</p>}
              {rate === null && <TextLink to="/settings/accounts">Set up a cloud account</TextLink>}</div>
            </div>
            <ComplianceTrend points={points} />
          </div>
        </section>
        <section className="ledger priority-ledger">
          <SectionHeading title="Priority findings" action={<TextLink to="/vulnerabilities">All findings</TextLink>} />
          {priority.length ? <ul>{priority.map(finding => <li key={finding.id}>
            <Link to={`/vulnerabilities?${new URLSearchParams({ finding: finding.id })}`} className="line-row priority-row">
              <span><span className="row-title">{finding.title}</span><small>{finding.resource_type} / {finding.resource_id}</small></span>
              <span className="priority-score"><Severity value={finding.severity} />{finding.cvss_score != null && <strong className="number">{finding.cvss_score.toFixed(1)}</strong>}</span>
            </Link>
          </li>)}</ul> : <EmptyState title="No critical or high findings found"><p>Findings from finished scans appear here.</p></EmptyState>}
        </section>
      </div>
      <div className="split dashboard-breakdowns">
        <section className="ledger">
          <SectionHeading title="Open findings by severity" />
          <dl className="severity-list">{severities.map(severity => <div key={severity} className="line-row">
            <dt>{severityLabels[severity]}</dt><dd><Meter value={count(severity) / maxSeverity * 100} label={`${count(severity)} ${severityLabels[severity].toLowerCase()} findings`} tone={severityTones[severity]} /><strong className="number">{count(severity)}</strong></dd>
          </div>)}</dl>
          {summary && summary.total_open_vulnerabilities > 0 && <p className="meta section-body">Average CVSS {summary.average_cvss_score.toFixed(1)}</p>}
        </section>
        <section className="ledger">
          <SectionHeading title="Framework scores" action={<TextLink to="/policies">View results</TextLink>} />
          {frameworkEntries.length ? <dl>{frameworkEntries.map(([name, score]) => <div key={name} className="line-row framework-row">
            <dt>{name.replace(/_/g, ' ')}</dt><dd className="meter-row"><Meter value={score} label={`${name} pass rate`} /><strong className="number">{score.toFixed(1).replace(/\.0$/, '')}%</strong></dd>
          </div>)}</dl> : <EmptyState title={frameworks ? 'No framework scores yet' : 'Framework scores unavailable'}><p>{frameworks ? 'Scores appear after a scan evaluates controls.' : 'Refresh to try loading the scores again.'}</p></EmptyState>}
        </section>
        <section className="ledger">
          <SectionHeading title="Open findings by resource" />
          {resources.length ? <dl>{resources.map(([resource, total]) => <div className="line-row" key={resource}><dt>{resource}</dt><dd className="number">{total}</dd></div>)}</dl>
            : <EmptyState title={summary ? 'No resource breakdown yet' : 'Resource breakdown unavailable'} />}
        </section>
      </div>
    </div>
  </div>;
}

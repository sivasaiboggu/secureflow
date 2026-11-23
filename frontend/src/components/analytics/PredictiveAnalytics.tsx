import { useState, type FormEvent } from 'react';
import { z } from 'zod/mini';
import { api } from '../../services/api';
import { apiMessage, Notice, PageHeader, SectionHeading, TextLink } from '../common/Workspace';

interface LogResult { is_threat: boolean; classification: string; confidence: number | null; method?: string }
interface EventContext { action?: string; actor?: string; region?: string; time?: string; bucket?: string }
interface MetricResult { is_anomaly?: boolean | null; anomaly_score?: number | null; algorithm?: string; method?: string; error?: string }

const sampleLog = JSON.stringify({
  eventVersion: '1.08',
  eventName: 'GetBucketLocation',
  userIdentity: { type: 'IAMUser' },
  requestParameters: { bucketName: 'example-backup-bucket' },
}, null, 2);
const sampleMetrics = '0.85, 0.92, 0.44, 0.12, 0.76, 0.99, 0.05, 0.81';
const logInput = z.string().check(z.trim(), z.minLength(1, 'Enter a log event to review.'));
const metricInput = z.array(z.number()).check(z.length(8));

function cloudTrailContext(payload: string): EventContext {
  try {
    const log = JSON.parse(payload);
    const string = (value: unknown) => typeof value === 'string' && value.trim() ? value : undefined;
    return {
      action: string(log?.eventName),
      actor: string(log?.userIdentity?.arn) ?? string(log?.userIdentity?.userName) ?? string(log?.userIdentity?.type),
      region: string(log?.awsRegion),
      time: string(log?.eventTime),
      bucket: string(log?.requestParameters?.bucketName),
    };
  } catch {
    return {};
  }
}

function MetricOutcome({ data }: { data: MetricResult }) {
  if (data.method === 'unavailable' || data.is_anomaly == null) {
    return <Notice tone="warning"><strong>Detector unavailable</strong><p>{data.error || 'Set up a local anomaly model to assess these metrics.'}</p></Notice>;
  }
  return <Notice tone={data.is_anomaly ? 'warning' : 'info'}>
    <strong>{data.is_anomaly ? 'Outlier flagged for review' : 'No outlier flag. Validation is still required.'}</strong>
    <p>Uncalibrated anomaly score: {data.anomaly_score?.toFixed(4) ?? 'unavailable'}</p>
    {data.algorithm && <p className="meta">Method: {data.algorithm}</p>}
  </Notice>;
}

export function PredictiveAnalytics() {
  const [logText, setLogText] = useState(sampleLog);
  const [metricsText, setMetricsText] = useState(sampleMetrics);
  const [logResult, setLogResult] = useState<{ result: LogResult; context: EventContext } | null>(null);
  const [metricResult, setMetricResult] = useState<MetricResult | null>(null);
  const [logError, setLogError] = useState('');
  const [metricError, setMetricError] = useState('');
  const [logLoading, setLogLoading] = useState(false);
  const [metricLoading, setMetricLoading] = useState(false);

  async function reviewLog(event: FormEvent) {
    event.preventDefault();
    setLogResult(null);
    setLogError('');
    const parsed = logInput.safeParse(logText);
    if (!parsed.success) {
      setLogError(parsed.error.issues[0].message);
      return;
    }
    setLogLoading(true);
    try {
      const { data } = await api.post<LogResult>('/vulnerabilities/analyze-log', { log_payload: logText });
      setLogResult({ result: data, context: cloudTrailContext(logText) });
    } catch (error) {
      setLogError(apiMessage(error, 'Could not review the log. Try again.'));
    } finally {
      setLogLoading(false);
    }
  }

  async function reviewMetrics(event: FormEvent) {
    event.preventDefault();
    setMetricResult(null);
    setMetricError('');
    const parsed = metricInput.safeParse(metricsText.split(',').map(value => value.trim() ? Number(value.trim()) : NaN));
    if (!parsed.success) {
      setMetricError('Enter exactly 8 numbers, separated by commas.');
      return;
    }
    setMetricLoading(true);
    try {
      const { data } = await api.post<MetricResult>('/vulnerabilities/analyze-metrics', { metrics: parsed.data });
      setMetricResult(data);
    } catch (error) {
      setMetricError(apiMessage(error, 'Could not check the metrics. Try again.'));
    } finally {
      setMetricLoading(false);
    }
  }

  return <div className="page">
    <PageHeader title="Log and metric review" description="Review CloudTrail events and metric readings. Scanner severity uses CVSS rules." />
    <div className="split analytics-split">
      <section className="ledger">
        <SectionHeading title="CloudTrail log review" />
        <form className="stack section-body" onSubmit={reviewLog} aria-busy={logLoading}>
          <p className="muted">Start with the sample or paste one CloudTrail event. A flag is a prompt to investigate.</p>
          <div className="field">
            <label htmlFor="log-payload">Event payload</label>
            <textarea id="log-payload" className="mono" rows={9} spellCheck={false} value={logText} onChange={event => setLogText(event.target.value)} />
          </div>
          <div className="form-actions">
            <button type="submit" className="button primary" disabled={logLoading}>{logLoading ? 'Reviewing…' : 'Review log'}</button>
            {logText !== sampleLog && <button type="button" className="button" disabled={logLoading} onClick={() => { setLogText(sampleLog); setLogError(''); setLogResult(null); }}>Load sample</button>}
          </div>
          {logError && <Notice tone="error">{logError}</Notice>}
          {logResult && <div className="stack">
            <Notice tone={logResult.result.is_threat ? 'warning' : 'info'}>
              <strong>{logResult.result.is_threat ? 'Flagged for review' : 'No flag. Review the event in context.'}</strong>
              {logResult.result.confidence != null && Number.isFinite(logResult.result.confidence) && <p>Uncalibrated score {logResult.result.confidence.toFixed(3)}</p>}
              {logResult.result.method && <p className="meta">{logResult.result.method.replace(/_/g, ' ')}</p>}
            </Notice>
            {Object.values(logResult.context).some(Boolean) && <dl className="event-context">
              {([['Action', logResult.context.action], ['Actor', logResult.context.actor], ['Region', logResult.context.region], ['Time', logResult.context.time]] as const)
                .map(([label, value]) => value && <div className="line-row" key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
              {logResult.context.bucket && <div className="line-row"><dt>Bucket</dt><dd><TextLink to={`/vulnerabilities?${new URLSearchParams({ q: logResult.context.bucket })}`}>{logResult.context.bucket}</TextLink></dd></div>}
            </dl>}
          </div>}
        </form>
      </section>
      <section className="ledger">
        <SectionHeading title="Metric anomaly check" />
        <form className="stack section-body" onSubmit={reviewMetrics} aria-busy={metricLoading}>
          <p className="muted">The check requires a trained local detector. Treat any outlier as a signal to investigate.</p>
          <div className="field">
            <label htmlFor="metric-values">Metric values</label>
            <input id="metric-values" className="mono" value={metricsText} aria-describedby="metric-hint" onChange={event => setMetricsText(event.target.value)} />
            <p className="meta" id="metric-hint">Enter 8 numbers separated by commas.</p>
          </div>
          <div className="form-actions"><button type="submit" className="button" disabled={metricLoading}>{metricLoading ? 'Checking…' : 'Check metrics'}</button></div>
          {metricError && <Notice tone="error">{metricError}</Notice>}
          {metricResult && <MetricOutcome data={metricResult} />}
        </form>
      </section>
    </div>
  </div>;
}

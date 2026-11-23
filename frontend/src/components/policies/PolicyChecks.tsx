import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { apiMessage, EmptyState, Notice, PageHeader, SectionHeading, Status } from '../common/Workspace';

interface Check {
  id: string;
  scan_id: string;
  framework: string;
  control_id: string;
  title: string;
  status: string;
  resource_id: string;
  checked_at: string | null;
  sample: boolean;
  control_level: boolean;
  violating_resources: string[];
}

interface Scan {
  id: string;
  completed_at: string | null;
  status: string;
}

const pageSize = 20;
const timeFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });

function checkedAt(date: string) {
  return timeFormat.format(new Date(/Z$|[+-]\d{2}:\d{2}$/i.test(date) ? date : date + 'Z'));
}

export function PolicyChecks() {
  const [params, setParams] = useSearchParams();
  const scan = params.get('scan') ?? '';
  const status = params.get('outcome') ?? '';
  const page = Math.max(0, Number.parseInt(params.get('page') ?? '', 10) || 0);
  const [scans, setScans] = useState<Scan[]>([]);
  const [checks, setChecks] = useState<Check[] | null>(null);
  const [scanError, setScanError] = useState(false);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const request = new AbortController();
    api.get<Scan[]>('/scans', { signal: request.signal }).then(({ data }) => {
      setScans(data.filter(item => ['COMPLETED', 'DEMO_COMPLETED'].includes(item.status)));
      setScanError(false);
    }).catch(() => { if (!request.signal.aborted) setScanError(true); });
    return () => request.abort();
  }, [reload]);

  useEffect(() => {
    const request = new AbortController();
    setChecks(null);
    setError('');
    api.get<Check[]>('/compliance/checks', {
      signal: request.signal,
      params: { finished_only: true, scan_id: scan || undefined, status: status || undefined, skip: page * pageSize, limit: pageSize + 1 },
    }).then(({ data }) => setChecks(data))
      .catch(error => { if (!request.signal.aborted) setError(apiMessage(error, 'Could not load policy checks.')); });
    return () => request.abort();
  }, [scan, status, page, reload]);

  function change(name: string, value: string) {
    const next = new URLSearchParams(params);
    if (name !== 'page') next.delete('page');
    if (value) next.set(name, value);
    else next.delete(name);
    setChecks(null);
    setParams(next);
  }

  return <div className="page policy-page">
    <PageHeader title="Policy checks" description="Review control results and resource evidence from finished scans." />
    <div className="policy-layout">
      <section className="ledger policy-filters">
        <SectionHeading title="Scope" />
        <div className="section-body stack">
          <div className="field">
            <label htmlFor="policy-scan">Scan run</label>
            <select id="policy-scan" value={scan} onChange={event => change('scan', event.target.value)}>
              <option value="">All finished scans</option>
              {scan && !scans.some(item => item.id === scan) && <option value={scan}>Scan {scan.slice(0, 8)}</option>}
              {scans.map(item => <option key={item.id} value={item.id}>
                {item.completed_at ? checkedAt(item.completed_at) : 'Date unavailable'} · {item.id.slice(0, 8)}{item.status === 'DEMO_COMPLETED' ? ' · Sample' : ''}
              </option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="policy-outcome">Outcome</label>
            <select id="policy-outcome" value={status} onChange={event => change('outcome', event.target.value)}>
              <option value="">Any outcome</option><option value="FAIL">Failed</option><option value="PASS">Passed</option>
            </select>
          </div>
          {scanError && <p className="meta" role="status">Could not load the scan list. <button className="text-link" type="button" onClick={() => setReload(n => n + 1)}>Retry</button></p>}
          <p className="meta">Control results reflect the selected scan. Resource evidence lists individual observations.</p>
        </div>
      </section>
      <section className="ledger">
        <SectionHeading title="Results" />
        {error ? <Notice tone="error">{error} <button className="text-link" type="button" onClick={() => setReload(n => n + 1)}>Retry</button></Notice>
          : !checks ? <LoadingSpinner label="Loading policy checks…" />
            : checks.length === 0 ? <EmptyState title="No checks in this view"><p>Change the filters or run a scan to collect results.</p></EmptyState>
              : <ul className="policy-results">{checks.slice(0, pageSize).map((check, index) => <li key={check.id} style={{ '--row-delay': `${Math.min(index, 4) * 40}ms` } as React.CSSProperties}>
                <details className="policy-check">
                  <summary>
                    <span className="policy-id">{check.framework.replace(/_/g, ' ')} {check.control_id}</span>
                    <span className="row-title">{check.title}</span>
                    <Status tone={check.status === 'PASS' ? 'success' : 'error'}>{check.status === 'PASS' ? 'Passed' : 'Failed'}</Status>
                  </summary>
                  <div className="policy-evidence stack">
                    <p className="meta">{check.control_level ? 'Control result' : 'Resource evidence'} · Scan {check.scan_id.slice(0, 8)}{check.sample ? ' · Sample scan' : ''}{check.checked_at ? ' · ' + checkedAt(check.checked_at) : ''}</p>
                    {check.control_level && check.status === 'PASS' ? <p>Account scope</p>
                      : <ul>{(check.violating_resources.length ? check.violating_resources : [check.resource_id]).map(resource => <li key={resource}>
                        <Link className="text-link" to={`/vulnerabilities?${new URLSearchParams({ q: resource })}`}>{resource}</Link>
                      </li>)}</ul>}
                  </div>
                </details>
              </li>)}</ul>}
        {(page > 0 || (checks?.length ?? 0) > pageSize) && <nav className="pagination" aria-label="Policy check pages">
          <button type="button" className="button" disabled={page === 0} onClick={() => change('page', page === 1 ? '' : String(page - 1))}>Previous</button>
          <span className="meta">Page {page + 1}</span>
          <button type="button" className="button" disabled={(checks?.length ?? 0) <= pageSize} onClick={() => change('page', String(page + 1))}>Next</button>
        </nav>}
      </section>
    </div>
  </div>;
}

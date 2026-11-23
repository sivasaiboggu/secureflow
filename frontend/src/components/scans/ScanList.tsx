import { useEffect, useState, type FormEvent } from 'react';
import { Plus } from 'lucide-react';
import { api } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { useToast } from '../common/ToastContext';
import { apiMessage, EmptyState, Meter, Notice, PageHeader, SectionHeading, Sheet, Status, TextLink } from '../common/Workspace';

interface Scan {
  id: string;
  cloud_account_id: string;
  status: string;
  progress: number;
  vulnerabilities_found: number;
  created_at: string;
}

interface CloudAccount { id: string; name: string; provider: string; is_active: boolean }

const scanStatuses: Record<string, { label: string; tone: string }> = {
  DEMO_COMPLETED: { label: 'Sample complete', tone: 'warning' },
  COMPLETED: { label: 'Completed', tone: 'success' },
  RUNNING: { label: 'Running', tone: 'accent' },
  PENDING: { label: 'Queued', tone: 'neutral' },
  FAILED: { label: 'Failed', tone: 'error' },
};

const dateTime = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' });

export function ScanList() {
  const { showToast } = useToast();
  const [scans, setScans] = useState<Scan[] | null>(null);
  const [accounts, setAccounts] = useState<CloudAccount[]>([]);
  const [scanError, setScanError] = useState('');
  const [accountError, setAccountError] = useState('');
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const request = new AbortController();
    let pending = false;
    async function refreshScans() {
      if (pending) return;
      pending = true;
      try {
        const { data } = await api.get<Scan[]>('/scans', { signal: request.signal });
        if (!request.signal.aborted) {
          setScans(data);
          setScanError('');
        }
      } catch (error) {
        if (!request.signal.aborted) setScanError(apiMessage(error, 'Could not load scan history.'));
      } finally {
        pending = false;
      }
    }
    void refreshScans();
    const interval = window.setInterval(() => { if (!document.hidden) void refreshScans(); }, 4000);
    const refreshWhenVisible = () => { if (!document.hidden) void refreshScans(); };
    document.addEventListener('visibilitychange', refreshWhenVisible);
    return () => {
      request.abort();
      window.clearInterval(interval);
      document.removeEventListener('visibilitychange', refreshWhenVisible);
    };
  }, [revision]);

  async function fetchAccounts(signal?: AbortSignal) {
    setAccountsLoading(true);
    setAccountError('');
    try {
      const { data } = await api.get<CloudAccount[]>('/scans/cloud-accounts', { signal });
      if (!signal?.aborted) setAccounts(data);
    } catch (error) {
      if (!signal?.aborted) setAccountError(apiMessage(error, 'Could not load cloud accounts.'));
    } finally {
      if (!signal?.aborted) setAccountsLoading(false);
    }
  }

  useEffect(() => {
    const request = new AbortController();
    void fetchAccounts(request.signal);
    return () => request.abort();
  }, []);

  const activeAccounts = accounts.filter(account => account.is_active);
  const validSelection = activeAccounts.some(account => account.id === selectedAccount);

  async function triggerScan(event: FormEvent) {
    event.preventDefault();
    if (submitting || !validSelection) return;
    setSubmitting(true);
    setSubmitError('');
    try {
      await api.post('/scans', { cloud_account_id: selectedAccount });
      setShowModal(false);
      showToast('Scan queued. The history updates as checks run.', 'success');
      setRevision(previous => previous + 1);
    } catch (error) {
      setSubmitError(apiMessage(error, 'Could not start the scan. Try again.'));
    } finally {
      setSubmitting(false);
    }
  }

  function openModal() {
    setSubmitError('');
    if (accountError && !accountsLoading) void fetchAccounts();
    setShowModal(true);
  }

  return <div className="page scan-page">
    <PageHeader title="Scans" description="Run checks against a cloud account and follow each run."
      action={<button type="button" className="button primary" onClick={openModal}><Plus size={18} aria-hidden="true" />New scan</button>} />
    <div className="stack">
      <p className="scope-note">Demo scans use sample data. Failed runs have no complete result. Completed runs cover the checks SecureFlow implements.</p>
      {scanError && <Notice tone="error">{scanError}{scans && ' Showing the last successful load.'}
        <div><button type="button" className="text-link" onClick={() => setRevision(previous => previous + 1)}>Retry</button></div>
      </Notice>}
      <section className="ledger">
        <SectionHeading title="Scan history" action={scans && <span className="meta">{scans.length} shown</span>} />
        {!scans && !scanError && <LoadingSpinner label="Loading scan history…" />}
        {scans?.length === 0 && <EmptyState title="No scans yet"><p>Choose a cloud account to run its first checks.</p><button type="button" className="text-link" onClick={openModal}>Start a scan</button></EmptyState>}
        {!!scans?.length && <div className="table-wrap" tabIndex={0} role="region" aria-label="Scan history table">
          <table className="ledger-table scan-table">
            <thead><tr><th scope="col">Cloud account</th><th scope="col">Status</th><th scope="col">Progress</th><th scope="col">Findings</th><th scope="col">Started</th><th scope="col">Results</th></tr></thead>
            <tbody>{scans.map(scan => {
              const account = accounts.find(account => account.id === scan.cloud_account_id);
              const status = scanStatuses[scan.status] || { label: scan.status, tone: 'neutral' };
              const finished = scan.status === 'COMPLETED' || scan.status === 'DEMO_COMPLETED';
              return <tr key={scan.id}>
                <td><span className="row-title" title={scan.cloud_account_id}>{account?.name || scan.cloud_account_id}</span><small className="mono" title={scan.id}>{scan.id.slice(0, 12)}{scan.id.length > 12 && '…'}</small>
                  <small className="table-mobile-detail">{Math.round(scan.progress)}% · {finished ? `${scan.vulnerabilities_found} findings` : scan.status === 'FAILED' ? 'Run failed' : 'Results pending'}</small>
                  <small className="table-mobile-detail">{dateTime.format(new Date(scan.created_at))}</small>
                  {finished && <span className="table-mobile-detail"><TextLink to={`/policies?${new URLSearchParams({ scan: scan.id })}`}>Checks</TextLink></span>}</td>
                <td><Status tone={status.tone}>{status.label}</Status></td>
                <td><div className="meter-row"><Meter value={scan.progress} label={`Progress for scan ${scan.id}`} tone={status.tone} /><span className="number">{Math.round(scan.progress)}%</span></div></td>
                <td className="number">{finished ? scan.vulnerabilities_found : '—'}</td>
                <td><time dateTime={scan.created_at}>{dateTime.format(new Date(scan.created_at))}</time></td>
                <td>{finished ? <TextLink to={`/policies?${new URLSearchParams({ scan: scan.id })}`}>Checks</TextLink> : '—'}</td>
              </tr>;
            })}</tbody>
          </table>
        </div>}
      </section>
    </div>
    {showModal && <Sheet title="Start a scan" closeLabel="Close scan dialog" onClose={() => { if (!submitting) setShowModal(false); }}>
      <form className="stack" onSubmit={triggerScan} aria-busy={submitting}>
        <div className="field">
          <label htmlFor="scan-account-select">Cloud account</label>
          <select id="scan-account-select" value={selectedAccount} onChange={event => setSelectedAccount(event.target.value)} required disabled={accountsLoading || submitting || !!accountError}>
            <option value="">{accountsLoading ? 'Loading accounts…' : 'Choose an account'}</option>
            {activeAccounts.map(account => <option key={account.id} value={account.id}>{account.name} · {account.provider.toUpperCase()}</option>)}
          </select>
        </div>
        {!accountsLoading && !accountError && !activeAccounts.length && <EmptyState title="No active cloud accounts"><TextLink to="/settings/accounts">Register an account</TextLink></EmptyState>}
        {accountError && <Notice tone="error">{accountError}<div><button type="button" className="text-link" onClick={() => void fetchAccounts()}>Retry</button></div></Notice>}
        {submitError && <Notice tone="error">{submitError}</Notice>}
        <div className="form-actions">
          <button type="submit" className="button primary" disabled={submitting || !validSelection || accountsLoading || !!accountError}>{submitting ? 'Starting…' : 'Start scan'}</button>
          <button type="button" className="button" onClick={() => setShowModal(false)} disabled={submitting}>Cancel</button>
        </div>
      </form>
    </Sheet>}
  </div>;
}

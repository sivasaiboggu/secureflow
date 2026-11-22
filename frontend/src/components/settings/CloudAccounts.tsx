import { useEffect, useState, type FormEvent } from 'react';
import { Cloud } from 'lucide-react';
import { z } from 'zod/mini';
import { api } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { apiMessage, EmptyState, Notice, PageHeader, SectionHeading, Status, TextLink } from '../common/Workspace';

interface CloudAccount { id: string; name: string; provider: string; is_active: boolean }
const providerNames: Record<string, string> = { aws: 'Amazon Web Services', gcp: 'Google Cloud Platform', azure: 'Microsoft Azure' };
const nameSchema = z.string().check(z.trim(), z.minLength(1, 'Enter an account name.'));
const keySchema = z.object({
  accessKey: z.string().check(z.trim(), z.minLength(1, 'Enter the AWS access key ID.')),
  secretKey: z.string().check(z.trim(), z.minLength(1, 'Enter the AWS secret access key.')),
});

export function CloudAccounts() {
  const [accounts, setAccounts] = useState<CloudAccount[]>([]);
  const [name, setName] = useState('');
  const [accessKey, setAccessKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [demo, setDemo] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loadError, setLoadError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  async function fetchAccounts(signal?: AbortSignal) {
    setLoading(true);
    try {
      const { data } = await api.get<CloudAccount[]>('/scans/cloud-accounts', { signal });
      if (!signal?.aborted) {
        setAccounts(data);
        setLoadError('');
      }
    } catch (error) {
      if (!signal?.aborted) setLoadError(apiMessage(error, 'Could not load cloud accounts.'));
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }

  useEffect(() => {
    const request = new AbortController();
    void fetchAccounts(request.signal);
    return () => request.abort();
  }, []);

  async function register(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage('');
    setError('');
    const accountName = nameSchema.safeParse(name);
    if (!accountName.success) {
      setError(accountName.error.issues[0].message);
      return;
    }
    const keys = keySchema.safeParse({ accessKey, secretKey });
    if (!demo && !keys.success) {
      setError(keys.error.issues[0].message);
      return;
    }
    const credentials = demo ? { scan_mode: 'demo' } : {
      scan_mode: 'real', aws_access_key_id: accessKey.trim(), aws_secret_access_key: secretKey.trim(),
    };
    setSubmitting(true);
    try {
      await api.post('/scans/cloud-accounts', { name: accountName.data, provider: 'aws', credentials });
      setMessage(demo ? 'Demo account saved. Its scans use sample data.' : 'Cloud account saved. Its credentials are checked during a live scan.');
      setName('');
      setAccessKey('');
      setSecretKey('');
      await fetchAccounts();
    } catch (error) {
      setError(apiMessage(error, 'Could not register the account. Try again.'));
    } finally {
      setSubmitting(false);
    }
  }

  return <div className="page accounts-page">
    <PageHeader title="Cloud accounts" description="Register an AWS account or use sample data to try a scan." />
    <div className="split settings-split">
      <section className="ledger">
        <SectionHeading title="Saved accounts" action={!loading && !loadError && <span className="meta">{accounts.length} shown</span>} />
        {loading && <LoadingSpinner label="Loading cloud accounts…" />}
        {!loading && loadError && <div className="section-body"><Notice tone="error">{loadError}
          <div><button type="button" className="text-link" onClick={() => void fetchAccounts()}>Retry</button></div>
        </Notice></div>}
        {!loading && !loadError && !accounts.length && <EmptyState title="No cloud accounts yet"><p>Register a demo account to run sample checks without AWS credentials.</p></EmptyState>}
        {!!accounts.length && <ul>{accounts.map(account => <li key={account.id} className="line-row account-row">
          <Cloud size={20} aria-hidden="true" />
          <span><span className="row-title">{account.name}</span><small>{providerNames[account.provider] || account.provider.toUpperCase()}</small></span>
          <Status tone={account.is_active ? 'success' : 'neutral'}>{account.is_active ? 'Active' : 'Inactive'}</Status>
        </li>)}</ul>}
      </section>
      <section className="ledger">
        <SectionHeading title="Register an account" />
        <form className="stack section-body" onSubmit={register} aria-busy={submitting}>
          {message && <Notice tone="success">{message}<div><TextLink to="/scans">Go to scans</TextLink></div></Notice>}
          {error && <Notice tone="error">{error}</Notice>}
          <div className="field">
            <label htmlFor="account-name">Account name</label>
            <input id="account-name" placeholder="Production AWS Account" required value={name} onChange={event => setName(event.target.value)} />
          </div>
          <label className="check-line"><input type="checkbox" checked={demo} onChange={event => setDemo(event.target.checked)} />
            <span><strong>Use sample data</strong><small className="row-title">Runs a demo without connecting to AWS.</small></span>
          </label>
          <div className="field">
            <label htmlFor="aws-access-key">AWS access key ID</label>
            <input id="aws-access-key" className="mono" autoComplete="off" spellCheck={false} required={!demo} disabled={demo}
              value={accessKey} onChange={event => setAccessKey(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="aws-secret-key">AWS secret access key</label>
            <input id="aws-secret-key" className="mono" type="password" autoComplete="off" required={!demo} disabled={demo}
              value={secretKey} onChange={event => setSecretKey(event.target.value)} />
          </div>
          {!demo && <p className="meta">The server needs <code>CLOUD_CREDENTIALS_KEY</code> to encrypt live credentials before storage.</p>}
          <div className="form-actions"><button type="submit" className="button primary" disabled={submitting}>{submitting ? 'Registering…' : 'Register account'}</button></div>
        </form>
      </section>
    </div>
  </div>;
}

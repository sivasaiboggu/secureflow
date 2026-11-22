import { useState, type FormEvent } from 'react';
import { Eye, EyeOff, ListChecks, ScanLine, ShieldAlert } from 'lucide-react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod/mini';
import { api, apiUnavailableReason, safeReturnTo, storeSession } from '../../services/api';
import { apiMessage, BrandMark, Notice } from '../common/Workspace';
import { ThemeButton } from '../common/ThemeButton';

const credentials = z.object({
  email: z.pipe(z.string().check(z.trim()), z.email('Enter a valid email address.')),
  password: z.string().check(z.minLength(1, 'Enter your password.')),
});

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { search } = useLocation();
  const query = new URLSearchParams(search);
  const returnTo = safeReturnTo(query.get('returnTo'));

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;
    const parsed = credentials.safeParse({ email, password });
    if (!parsed.success) {
      setError(parsed.error.issues[0].message);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({ username: parsed.data.email, password: parsed.data.password });
      const response = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      storeSession(response.data);
      navigate(returnTo, { replace: true });
    } catch (error) {
      setError(apiMessage(error, apiUnavailableReason || 'Could not sign in. Check your connection and try again.'));
    } finally {
      setLoading(false);
    }
  }

  if (localStorage.getItem('token')) return <Navigate to={returnTo} replace />;

  return <div className="login-page">
    <header className="login-bar">
      <span className="brand"><BrandMark />SecureFlow</span>
      <ThemeButton />
    </header>
    <div className="login-grid">
      <section className="login-form-section">
        <div className="login-form">
          <div><h1>Sign in</h1><p className="muted">Use your organization’s SecureFlow account.</p></div>
          {query.has('expired') && <Notice>Your session ended. Sign in to return to your last view.</Notice>}
          {error && <Notice tone="error">{error}</Notice>}
          <form className="stack" onSubmit={handleLogin} aria-busy={loading}>
            <div className="field">
              <label htmlFor="login-email">Email address</label>
              <input id="login-email" type="email" autoComplete="username" autoCapitalize="none" spellCheck={false} required value={email} onChange={event => setEmail(event.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="login-password">Password</label>
              <div className="password-field">
                <input id="login-password" type={visible ? 'text' : 'password'} autoComplete="current-password" required value={password} onChange={event => setPassword(event.target.value)} />
                <button type="button" className="button icon-button" aria-label={visible ? 'Hide password' : 'Show password'} onClick={() => setVisible(value => !value)}>
                  {visible ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
                </button>
              </div>
            </div>
            <button id="login-submit" type="submit" className="button primary" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
          </form>
        </div>
      </section>
      <section className="login-intro">
        <h2>AWS security console</h2>
        <p className="muted">Review what your scans found and record how you’re handling each issue.</p>
        <ul className="login-capabilities">
          <li><ScanLine size={18} aria-hidden="true" /><span><strong>Run a scan</strong><small>Check resources in a connected AWS account.</small></span></li>
          <li><ShieldAlert size={18} aria-hidden="true" /><span><strong>Triage findings</strong><small>Review evidence and save Terraform plans.</small></span></li>
          <li><ListChecks size={18} aria-hidden="true" /><span><strong>Review policy checks</strong><small>See which CIS controls passed by scan.</small></span></li>
        </ul>
      </section>
    </div>
    <footer className="login-footer">
      <Link className="text-link" to="/privacy">Data and privacy</Link>
      <Link className="text-link" to="/usage">Usage scope</Link>
    </footer>
  </div>;
}

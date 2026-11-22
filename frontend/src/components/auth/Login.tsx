import { useState, type FormEvent } from 'react';
import { ArrowRight } from 'lucide-react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { z } from 'zod/mini';
import { api, apiUnavailableReason } from '../../services/api';
import { apiMessage, BrandMark, Notice } from '../common/Workspace';
import { ThemeButton } from '../common/ThemeButton';

const credentials = z.object({
  email: z.pipe(z.string().check(z.trim()), z.email('Enter a valid email address.')),
  password: z.string().check(z.minLength(1, 'Enter your password.')),
});

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
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
      localStorage.setItem('token', response.data.access_token);
      if (response.data.refresh_token) localStorage.setItem('refresh_token', response.data.refresh_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      navigate('/dashboard', { replace: true });
    } catch (error) {
      setError(apiMessage(error, apiUnavailableReason || 'Could not sign in. Check your connection and try again.'));
    } finally {
      setLoading(false);
    }
  }

  if (localStorage.getItem('token')) return <Navigate to="/dashboard" replace />;

  return <div className="login-page">
    <header className="login-bar">
      <span className="brand"><BrandMark />SecureFlow</span>
      <ThemeButton />
    </header>
    <div className="login-grid">
      <section className="login-intro text-ink">
        <h2>Review your<br /> AWS posture.</h2>
        <p>Run cloud checks, investigate findings and save Terraform plans for review.</p>
        <div className="login-rules" aria-hidden="true"><i /><i /><i /><i /><i /></div>
        <p className="login-scope"><span>7 AWS scanners</span><span>8 CIS controls</span></p>
      </section>
      <section className="login-form-section">
        <div className="login-form">
          <div><h1>Sign in</h1><p className="muted">Use your organization’s SecureFlow account.</p></div>
          {error && <Notice tone="error">{error}</Notice>}
          <form className="stack" onSubmit={handleLogin} aria-busy={loading}>
            <div className="field">
              <label htmlFor="login-email">Email address</label>
              <input id="login-email" type="email" autoComplete="username" required value={email} onChange={event => setEmail(event.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="login-password">Password</label>
              <input id="login-password" type="password" autoComplete="current-password" required value={password} onChange={event => setPassword(event.target.value)} />
            </div>
            <button id="login-submit" type="submit" className="button primary" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'} <ArrowRight size={17} aria-hidden="true" />
            </button>
          </form>
        </div>
      </section>
    </div>
    <footer className="login-footer">
      <Link className="text-link" to="/privacy">Data and privacy</Link>
      <Link className="text-link" to="/usage">Usage scope</Link>
    </footer>
  </div>;
}

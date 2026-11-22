import React, { useEffect, useState } from 'react';
import { useMediaQuery } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { api } from '../../services/api';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  // Below 768px the two-column layout stacks: the 420px form column
  // used to squeeze the brand panel and overflow a phone viewport.
  const narrow = useMediaQuery('(max-width: 768px)');

  // A valid session already exists: never show the sign-in form to a
  // signed-in user (an expired token is cleared by the API interceptor
  // on the first failed refresh, so this cannot loop).
  useEffect(() => {
    if (localStorage.getItem('token')) navigate('/dashboard', { replace: true });
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);

      const response = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      localStorage.setItem('token', response.data.access_token);
      if (response.data.refresh_token) {
        localStorage.setItem('refresh_token', response.data.refresh_token);
      }
      localStorage.setItem('user', JSON.stringify(response.data.user));
      navigate('/dashboard');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Connection failed. Ensure the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ ...styles.root, ...(narrow ? { flexDirection: 'column' as const } : {}) }}>
      {/* Left brand panel */}
      <div style={{
        ...styles.brandPanel,
        ...(narrow ? { flex: 'none', padding: '32px 24px 24px', borderRight: 'none', borderBottom: '0.8px solid var(--nexus-border-soft)' } : {}),
      }}>
        <div style={{ ...styles.brandContent, ...(narrow ? { paddingTop: 8, gap: 24 } : {}) }}>
          {/* Logo mark */}
          <div style={styles.logoMark}>
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <polygon points="20,2 38,12 38,28 20,38 2,28 2,12" fill="none" stroke="#E7FF72" strokeWidth="1.5"/>
              <polygon points="20,8 32,15 32,25 20,32 8,25 8,15" fill="rgba(231,255,114,0.12)" stroke="#E7FF72" strokeWidth="0.8"/>
              <circle cx="20" cy="20" r="4" fill="#E7FF72"/>
            </svg>
          </div>

          <div style={styles.brandTag}>NEXUS SECUREFLOW</div>

          <h1 style={{ ...styles.displayText, ...(narrow ? { fontSize: 'clamp(40px, 11vw, 48px)' } : {}) }}>
            Cloud security<br />
            <span style={{ color: '#E7FF72' }}>posture, in</span><br />
            one place.
          </h1>

          <p style={styles.brandSub}>
            SCAN YOUR CLOUD ACCOUNTS, REVIEW THE FINDINGS,<br />
            AND TRACK COMPLIANCE FROM ONE DASHBOARD.
          </p>

        </div>

          {/* Bottom facts strip — the ledger line, repeated from the
              dashboard: a hairline rule, a 2px lime segment, and real
              numbers from the product (7 AWS scanners, 8 CIS controls
              evaluated per scan, Terraform fixes included). The old
              row here was four decorative tab labels that did nothing. */}
        <div style={styles.factsStrip}>
          <div style={styles.factsRule} />
          <p style={styles.factsText}>
            <span style={styles.factsNumber}>7</span> AWS SCANNERS&nbsp;&nbsp;·&nbsp;&nbsp;
            <span style={styles.factsNumber}>8</span> CIS CONTROLS PER SCAN&nbsp;&nbsp;·&nbsp;&nbsp;
            TERRAFORM FIXES INCLUDED
          </p>
        </div>
      </div>

      {/* Right login form */}
      <div style={{
        ...styles.formPanel,
        ...(narrow ? { flex: 'none', width: '100%', padding: '32px 24px 48px' } : {}),
      }}>
        <div style={styles.formCard}>
          <div style={styles.cardInner}>
            <div style={styles.formLogo}>
              <svg width="28" height="28" viewBox="0 0 40 40" fill="none">
                <polygon points="20,2 38,12 38,28 20,38 2,28 2,12" fill="none" stroke="#E7FF72" strokeWidth="1.5"/>
                <circle cx="20" cy="20" r="5" fill="#E7FF72"/>
              </svg>
            </div>

            <p style={styles.formMono}>SECUREFLOW SIGN IN</p>
            <h2 style={styles.formTitle}>Sign in</h2>
            <p style={styles.formSub}>Sign in to review your scans, findings, and compliance checks.</p>

            {error && (
              <div style={styles.errorBox}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                  <circle cx="12" cy="12" r="10" stroke="var(--sev-critical)" strokeWidth="1.5"/>
                  <line x1="12" y1="8" x2="12" y2="13" stroke="var(--sev-critical)" strokeWidth="1.5" strokeLinecap="round"/>
                  <circle cx="12" cy="16.5" r="0.8" fill="var(--sev-critical)"/>
                </svg>
                <span style={{ fontSize: 12, color: 'var(--sev-critical)', fontFamily: 'Geist Mono, monospace', letterSpacing: '0.05em' }}>
                  {error}
                </span>
              </div>
            )}

            <form onSubmit={handleLogin} style={styles.form}>
              <div style={styles.fieldGroup}>
                <label htmlFor="login-email" style={styles.fieldLabel}>EMAIL ADDRESS</label>
                <input
                  id="login-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={styles.input}
                  placeholder="you@company.com"
                  onFocus={(e) => { e.currentTarget.style.borderColor = 'rgba(231,255,114,0.5)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(231,255,114,0.08)'; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--nexus-border-strong)'; e.currentTarget.style.boxShadow = 'none'; }}
                />
              </div>

              <div style={styles.fieldGroup}>
                <label htmlFor="login-password" style={styles.fieldLabel}>PASSWORD</label>
                <input
                  id="login-password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={styles.input}
                  placeholder="••••••••••"
                  onFocus={(e) => { e.currentTarget.style.borderColor = 'rgba(231,255,114,0.5)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(231,255,114,0.08)'; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--nexus-border-strong)'; e.currentTarget.style.boxShadow = 'none'; }}
                />
              </div>

              <button
                id="login-submit"
                type="submit"
                disabled={loading}
                style={{
                  ...styles.submitBtn,
                  opacity: loading ? 0.7 : 1,
                  cursor: loading ? 'not-allowed' : 'pointer',
                }}
                onMouseEnter={(e) => !loading && (e.currentTarget.style.boxShadow = '0 8px 28px rgba(231,255,114,0.4)')}
                onMouseLeave={(e) => (e.currentTarget.style.boxShadow = 'none')}
              >
                {loading ? (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}>
                    <span style={styles.spinner} />
                    SIGNING IN...
                  </span>
                ) : (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}>
                    SIGN IN
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                      <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </span>
                )}
              </button>
            </form>

            
          </div>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  root: {
    display: 'flex',
    minHeight: '100vh',
    width: '100%',
    position: 'relative',
    zIndex: 1,
    fontFamily: '"Geist", sans-serif',
  },
  brandPanel: {
    flex: '1 1 55%',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: '48px 56px',
    borderRight: '0.8px solid var(--nexus-border-soft)',
    position: 'relative',
  },
  brandContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: 32,
    maxWidth: 560,
    paddingTop: 40,
  },
  logoMark: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  brandTag: {
    fontFamily: '"Geist Mono", monospace',
    fontSize: 10,
    fontWeight: 500,
    letterSpacing: '0.28em',
    textTransform: 'uppercase' as const,
    color: 'var(--nexus-text-muted)',
  },
  displayText: {
    fontSize: 'clamp(48px, 5vw, 80px)',
    fontWeight: 500,
    lineHeight: 1.0,
    letterSpacing: '-0.05em',
    color: 'var(--nexus-text-primary)',
    margin: 0,
  },
  brandSub: {
    fontFamily: '"Geist Mono", monospace',
    fontSize: 11,
    fontWeight: 500,
    lineHeight: '20px',
    letterSpacing: '0.18em',
    textTransform: 'uppercase' as const,
    color: 'var(--nexus-text-muted)',
  },
  factsStrip: {
    borderTop: '0.8px solid var(--nexus-border-strong)',
    paddingTop: 16,
  },
  factsRule: {
    width: 32,
    height: 2,
    background: 'var(--nexus-accent-bar)',
    marginBottom: 12,
  },
  factsText: {
    fontFamily: '"Geist Mono", monospace',
    fontSize: 10,
    letterSpacing: '0.14em',
    color: 'var(--nexus-text-muted)',
    margin: 0,
  },
  factsNumber: {
    color: 'var(--nexus-text-primary)',
    fontWeight: 700,
  },
  formPanel: {
    flex: '0 0 420px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '48px 40px',
  },
  formCard: {
    width: '100%',
    maxWidth: 360,
    position: 'relative',
  },
  cardInner: {
    position: 'relative',
    zIndex: 1,
    background: 'var(--nexus-surface)',
    border: '0.8px solid var(--nexus-border)',
    borderRadius: 16,
    padding: '36px 32px',
    boxShadow: 'rgba(0,0,0,0.45) 0px 18px 60px 0px, var(--nexus-elevated-bg) 0px 1px 0px 0px inset',
  },
  formLogo: {
    marginBottom: 20,
  },
  formMono: {
    fontFamily: '"Geist Mono", monospace',
    fontSize: 9,
    fontWeight: 500,
    letterSpacing: '0.28em',
    textTransform: 'uppercase' as const,
    color: 'var(--nexus-text-muted)',
    marginBottom: 8,
  },
  formTitle: {
    fontSize: 28,
    fontWeight: 500,
    letterSpacing: '-0.04em',
    color: 'var(--nexus-text-primary)',
    marginBottom: 6,
  },
  formSub: {
    fontSize: 13,
    color: 'var(--nexus-text-muted)',
    marginBottom: 28,
    lineHeight: 1.5,
  },
  errorBox: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 8,
    background: 'rgba(239,68,68,0.1)',
    border: '0.8px solid rgba(239,68,68,0.3)',
    borderRadius: 8,
    padding: '10px 12px',
    marginBottom: 20,
  },
  form: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 16,
  },
  fieldGroup: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 6,
  },
  fieldLabel: {
    fontFamily: '"Geist Mono", monospace',
    fontSize: 9,
    fontWeight: 600,
    letterSpacing: '0.2em',
    textTransform: 'uppercase' as const,
    color: 'var(--nexus-text-muted)',
  },
  input: {
    background: 'var(--nexus-input-bg)',
    border: '0.8px solid var(--nexus-border-strong)',
    borderRadius: 10,
    padding: '11px 14px',
    fontSize: 14,
    fontFamily: '"Geist", sans-serif',
    color: 'var(--nexus-text-primary)',
    outline: 'none',
    transition: 'border-color 150ms ease, box-shadow 150ms ease',
    width: '100%',
  },
  submitBtn: {
    width: '100%',
    background: '#E7FF72',
    color: '#080b12',
    border: 'none',
    borderRadius: 10,
    padding: '13px 20px',
    fontSize: 12,
    fontWeight: 700,
    fontFamily: '"Geist Mono", monospace',
    letterSpacing: '0.16em',
    textTransform: 'uppercase' as const,
    cursor: 'pointer',
    transition: 'all 150ms ease',
    marginTop: 8,
  },
  spinner: {
    display: 'inline-block',
    width: 12,
    height: 12,
    border: '2px solid var(--nexus-border-strong)',
    borderTopColor: '#080b12',
    borderRadius: '50%',
    animation: 'spin 0.7s linear infinite',
  },
};

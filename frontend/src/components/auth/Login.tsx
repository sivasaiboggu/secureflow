import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../services/api';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('admin@secureflow.io');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

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
      localStorage.setItem('user', JSON.stringify(response.data.user));
      navigate('/dashboard');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Connection failed. Ensure the backend is running on port 8080.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.root}>
      {/* Left brand panel */}
      <div style={styles.brandPanel}>
        <div style={styles.brandContent}>
          {/* Logo mark */}
          <div style={styles.logoMark}>
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <polygon points="20,2 38,12 38,28 20,38 2,28 2,12" fill="none" stroke="#E7FF72" strokeWidth="1.5"/>
              <polygon points="20,8 32,15 32,25 20,32 8,25 8,15" fill="rgba(231,255,114,0.12)" stroke="#E7FF72" strokeWidth="0.8"/>
              <circle cx="20" cy="20" r="4" fill="#E7FF72"/>
            </svg>
          </div>

          <div style={styles.brandTag}>NEXUS SECUREFLOW</div>

          <h1 style={styles.displayText}>
            Security<br />
            <span style={{ color: '#E7FF72' }}>powered by</span><br />
            intelligence.
          </h1>

          <p style={styles.brandSub}>
            EMBED ULTRA-FAST, CONTEXT-AWARE CLOUD<br />
            SECURITY INTO YOUR ARCHITECTURE WITH<br />
            OUR LASER-FOCUSED POSTURE ENGINE.
          </p>

          {/* Stats row */}
          <div style={styles.statsRow}>
            {[
              { value: '99.9%', label: 'Uptime SLA' },
              { value: '<2ms', label: 'Scan Latency' },
              { value: '500+', label: 'CIS Controls' },
            ].map((s) => (
              <div key={s.label} style={styles.statItem}>
                <span style={styles.statValue}>{s.value}</span>
                <span style={styles.statLabel}>{s.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom nav-like tabs */}
        <div style={styles.tabRow}>
          {['Platform', 'Architecture', 'Metrics', 'Logs'].map((t, i) => (
            <div key={t} style={{ ...styles.tab, ...(i === 0 ? styles.tabActive : {}) }}>{t}</div>
          ))}
        </div>
      </div>

      {/* Right login form */}
      <div style={styles.formPanel}>
        <div style={styles.formCard}>
          {/* Card gradient shell */}
          <div style={styles.cardShell} />

          <div style={styles.cardInner}>
            <div style={styles.formLogo}>
              <svg width="28" height="28" viewBox="0 0 40 40" fill="none">
                <polygon points="20,2 38,12 38,28 20,38 2,28 2,12" fill="none" stroke="#E7FF72" strokeWidth="1.5"/>
                <circle cx="20" cy="20" r="5" fill="#E7FF72"/>
              </svg>
            </div>

            <p style={styles.formMono}>NEXUS IDENTITY VERIFICATION</p>
            <h2 style={styles.formTitle}>Initialize System</h2>
            <p style={styles.formSub}>Authenticate to access the security posture engine</p>

            {error && (
              <div style={styles.errorBox}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                  <circle cx="12" cy="12" r="10" stroke="#f87171" strokeWidth="1.5"/>
                  <line x1="12" y1="8" x2="12" y2="13" stroke="#f87171" strokeWidth="1.5" strokeLinecap="round"/>
                  <circle cx="12" cy="16.5" r="0.8" fill="#f87171"/>
                </svg>
                <span style={{ fontSize: 12, color: '#f87171', fontFamily: 'Geist Mono, monospace', letterSpacing: '0.05em' }}>
                  {error}
                </span>
              </div>
            )}

            <form onSubmit={handleLogin} style={styles.form}>
              <div style={styles.fieldGroup}>
                <label style={styles.fieldLabel}>EMAIL ADDRESS</label>
                <input
                  id="login-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={styles.input}
                  placeholder="admin@secureflow.io"
                  onFocus={(e) => { e.currentTarget.style.borderColor = 'rgba(231,255,114,0.5)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(231,255,114,0.08)'; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = 'rgba(244,240,232,0.15)'; e.currentTarget.style.boxShadow = 'none'; }}
                />
              </div>

              <div style={styles.fieldGroup}>
                <label style={styles.fieldLabel}>PASSWORD</label>
                <input
                  id="login-password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={styles.input}
                  placeholder="••••••••••"
                  onFocus={(e) => { e.currentTarget.style.borderColor = 'rgba(231,255,114,0.5)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(231,255,114,0.08)'; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = 'rgba(244,240,232,0.15)'; e.currentTarget.style.boxShadow = 'none'; }}
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
                    AUTHENTICATING...
                  </span>
                ) : (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}>
                    INITIALIZE SYSTEM
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                      <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </span>
                )}
              </button>
            </form>

            <div style={styles.hint}>
              <span style={styles.hintMono}>DEFAULT CREDENTIALS</span>
              <code style={styles.hintCode}>admin@secureflow.io / password123</code>
            </div>
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
    borderRight: '0.8px solid rgba(244,240,232,0.08)',
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
    color: 'rgba(158,163,160,0.7)',
  },
  displayText: {
    fontSize: 'clamp(48px, 5vw, 80px)',
    fontWeight: 500,
    lineHeight: 1.0,
    letterSpacing: '-0.05em',
    color: '#F4F0E8',
    margin: 0,
  },
  brandSub: {
    fontFamily: '"Geist Mono", monospace',
    fontSize: 11,
    fontWeight: 500,
    lineHeight: '20px',
    letterSpacing: '0.18em',
    textTransform: 'uppercase' as const,
    color: 'rgba(158,163,160,0.65)',
  },
  statsRow: {
    display: 'flex',
    gap: 48,
    marginTop: 8,
  },
  statItem: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 4,
  },
  statValue: {
    fontSize: 28,
    fontWeight: 600,
    letterSpacing: '-0.03em',
    color: '#E7FF72',
  },
  statLabel: {
    fontFamily: '"Geist Mono", monospace',
    fontSize: 10,
    letterSpacing: '0.16em',
    textTransform: 'uppercase' as const,
    color: 'rgba(158,163,160,0.65)',
  },
  tabRow: {
    display: 'flex',
    gap: 4,
    alignItems: 'center',
  },
  tab: {
    fontFamily: '"Geist Mono", monospace',
    fontSize: 11,
    letterSpacing: '0.12em',
    textTransform: 'uppercase' as const,
    color: 'rgba(158,163,160,0.6)',
    padding: '6px 14px',
    borderRadius: 0,
    cursor: 'pointer',
    borderBottom: '0.8px solid transparent',
  },
  tabActive: {
    color: '#F4F0E8',
    borderBottom: '0.8px solid rgba(244,240,232,0.4)',
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
  cardShell: {
    position: 'absolute',
    inset: -1,
    borderRadius: 16,
    background: 'radial-gradient(ellipse at top, rgba(244,240,232,0.18) 0.5px, transparent 0.5px)',
    pointerEvents: 'none',
    zIndex: 0,
  },
  cardInner: {
    position: 'relative',
    zIndex: 1,
    background: 'rgba(14,18,27,0.85)',
    backdropFilter: 'blur(24px)',
    WebkitBackdropFilter: 'blur(24px)',
    border: '0.8px solid rgba(244,240,232,0.12)',
    borderRadius: 16,
    padding: '36px 32px',
    boxShadow: 'rgba(0,0,0,0.45) 0px 18px 60px 0px, rgba(255,255,255,0.06) 0px 1px 0px 0px inset',
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
    color: 'rgba(158,163,160,0.6)',
    marginBottom: 8,
  },
  formTitle: {
    fontSize: 28,
    fontWeight: 500,
    letterSpacing: '-0.04em',
    color: '#F4F0E8',
    marginBottom: 6,
  },
  formSub: {
    fontSize: 13,
    color: 'rgba(158,163,160,0.75)',
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
    color: 'rgba(158,163,160,0.7)',
  },
  input: {
    background: 'rgba(255,255,255,0.04)',
    border: '0.8px solid rgba(244,240,232,0.15)',
    borderRadius: 10,
    padding: '11px 14px',
    fontSize: 14,
    fontFamily: '"Geist", sans-serif',
    color: '#F4F0E8',
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
    border: '2px solid rgba(8,11,18,0.3)',
    borderTopColor: '#080b12',
    borderRadius: '50%',
    animation: 'spin 0.7s linear infinite',
  },
  hint: {
    marginTop: 24,
    padding: '12px 14px',
    background: 'rgba(255,255,255,0.03)',
    border: '0.8px solid rgba(244,240,232,0.08)',
    borderRadius: 8,
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 6,
  },
  hintMono: {
    fontFamily: '"Geist Mono", monospace',
    fontSize: 9,
    letterSpacing: '0.22em',
    textTransform: 'uppercase' as const,
    color: 'rgba(158,163,160,0.5)',
  },
  hintCode: {
    fontFamily: '"Geist Mono", monospace',
    fontSize: 11,
    color: 'rgba(231,255,114,0.7)',
    letterSpacing: '0.05em',
  },
};

import React, { useEffect, useState } from 'react';
import { CircularProgress, Box } from '@mui/material';
import { api } from '../../services/api';

interface CloudAccount {
  id: string;
  name: string;
  provider: string;
  is_active: boolean;
}

const providerIcon: Record<string, string> = {
  aws: '☁',
  gcp: '◆',
  azure: '▲',
};

const providerLabel: Record<string, string> = {
  aws: 'Amazon Web Services',
  gcp: 'Google Cloud Platform',
  azure: 'Microsoft Azure',
};

export const CloudAccounts: React.FC = () => {
  const [accounts, setAccounts] = useState<CloudAccount[]>([]);
  const [name, setName] = useState('');
  const [provider, setProvider] = useState('aws');
  const [accessKey, setAccessKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [demo, setDemo] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);

  useEffect(() => { fetchAccounts(); }, []);

  const fetchAccounts = async () => {
    try {
      const res = await api.get('/scans/cloud-accounts');
      setAccounts(res.data);
    } catch (err) { console.error(err); }
    finally { setPageLoading(false); }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(''); setError(''); setLoading(true);
    try {
      await api.post('/scans/cloud-accounts', {
        name, provider,
        credentials: demo ? { scan_mode: "demo" } : { scan_mode: "real", aws_access_key_id: accessKey, aws_secret_access_key: secretKey }
      });
      setMessage(demo ? 'Demo account saved. Its findings are sample data, not an AWS assessment.' : 'Cloud account saved. Credentials have not yet been verified.');
      setName(''); setAccessKey(''); setSecretKey('');
      fetchAccounts();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to register account.');
    } finally { setLoading(false); }
  };

  if (pageLoading) return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
      <CircularProgress size={40} sx={{ color: '#E7FF72' }} />
    </Box>
  );

  return (
    <div className="accounts-page" style={{ padding: '32px', maxWidth: 1400, margin: '0 auto' }}>
      <div style={{ marginBottom: 40 }}>
        <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.28em', textTransform: 'uppercase' as const, color: 'rgba(158,163,160,0.6)', marginBottom: 8 }}>INTEGRATIONS</p>
        <h1 style={{ fontFamily: '"Geist", sans-serif', fontSize: 32, fontWeight: 500, letterSpacing: '-0.04em', color: '#F4F0E8', margin: 0 }}>Cloud Accounts</h1>
      </div>

      <div className="accounts-grid" style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 20, alignItems: 'start' }}>
        {/* Form panel */}
        <div style={{ background: 'rgba(14,18,27,0.8)', backdropFilter: 'blur(24px)', border: '0.8px solid rgba(244,240,232,0.1)', borderRadius: 12, padding: 28 }}>
          <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase' as const, color: 'rgba(158,163,160,0.55)', marginBottom: 20 }}>REGISTER NEW ACCOUNT</p>

          {message && (
            <div style={{ background: 'rgba(74,222,128,0.1)', border: '0.8px solid rgba(74,222,128,0.3)', borderRadius: 8, padding: '10px 14px', marginBottom: 16 }}>
              <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 11, color: '#4ade80', letterSpacing: '0.05em' }}>✓ {message}</p>
            </div>
          )}
          {error && (
            <div style={{ background: 'rgba(239,68,68,0.1)', border: '0.8px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '10px 14px', marginBottom: 16 }}>
              <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 11, color: '#f87171', letterSpacing: '0.05em' }}>⚠ {error}</p>
            </div>
          )}

          <form onSubmit={handleAdd} style={{ display: 'flex', flexDirection: 'column' as const, gap: 16 }}>
            <div>
              <label style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase' as const, color: 'rgba(158,163,160,0.65)', display: 'block', marginBottom: 8 }}>Account Name</label>
              <input required value={name} onChange={(e) => setName(e.target.value)}
                style={{ width: '100%', background: 'rgba(255,255,255,0.04)', border: '0.8px solid rgba(244,240,232,0.15)', borderRadius: 10, padding: '11px 14px', fontSize: 13, fontFamily: '"Geist", sans-serif', color: '#F4F0E8', outline: 'none', boxSizing: 'border-box' as const }}
                placeholder="Production AWS Account" />
            </div>

            <div>
              <label style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase' as const, color: 'rgba(158,163,160,0.65)', display: 'block', marginBottom: 8 }}>Provider</label>
              <div style={{ display: 'flex', gap: 8 }}>
                {['aws'].map((p) => (
                  <button key={p} type="button" onClick={() => setProvider(p)}
                    style={{
                      flex: 1, background: provider === p ? 'rgba(231,255,114,0.12)' : 'rgba(255,255,255,0.04)',
                      border: `0.8px solid ${provider === p ? 'rgba(231,255,114,0.35)' : 'rgba(244,240,232,0.12)'}`,
                      borderRadius: 8, padding: '9px 8px', color: provider === p ? '#E7FF72' : '#9EA3A0',
                      fontFamily: '"Geist Mono", monospace', fontSize: 10, letterSpacing: '0.12em', cursor: 'pointer', transition: 'all 150ms ease',
                    }}
                  >
                    {p.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <label style={{ display: 'flex', gap: 10, lineHeight: 1.6, fontSize: 13, color: '#F4F0E8' }}>
              <input type="checkbox" checked={demo} onChange={e => setDemo(e.target.checked)} />
              Use sample data (demo). No AWS access or security assessment.
            </label>
            <p style={{ color: '#9EA3A0', fontSize: 12, lineHeight: 1.6 }}>AWS only. Other providers are not ready. Live credentials are stored in the app database without application-level encryption. Use only a local test account until secret storage is hardened.</p>
            <div>
              <label htmlFor="aws-access-key" style={{ fontSize: 12, color: '#9EA3A0' }}>AWS access key ID</label>
              <input id="aws-access-key" aria-label="AWS access key ID" required={!demo} disabled={demo} value={accessKey} onChange={(e) => setAccessKey(e.target.value)}
                style={{ width: '100%', background: 'rgba(255,255,255,0.04)', border: '0.8px solid rgba(244,240,232,0.15)', borderRadius: 10, padding: '11px 14px', fontSize: 12, fontFamily: '"Geist Mono", monospace', color: '#F4F0E8', outline: 'none', boxSizing: 'border-box' as const }}
                placeholder="AKIA..." />
            </div>

            <div>
              <label style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase' as const, color: 'rgba(158,163,160,0.65)', display: 'block', marginBottom: 8 }}>Secret Access Key</label>
              <input aria-label="AWS secret access key" required={!demo} disabled={demo} type="password" value={secretKey} onChange={(e) => setSecretKey(e.target.value)}
                style={{ width: '100%', background: 'rgba(255,255,255,0.04)', border: '0.8px solid rgba(244,240,232,0.15)', borderRadius: 10, padding: '11px 14px', fontSize: 12, fontFamily: '"Geist Mono", monospace', color: '#F4F0E8', outline: 'none', boxSizing: 'border-box' as const }}
                placeholder="••••••••••••••••" />
            </div>

            <button type="submit" disabled={loading}
              style={{ background: '#E7FF72', color: '#080b12', border: 'none', borderRadius: 10, padding: '13px 20px', fontSize: 11, fontWeight: 700, fontFamily: '"Geist Mono", monospace', letterSpacing: '0.16em', textTransform: 'uppercase' as const, cursor: 'pointer', marginTop: 4, transition: 'all 150ms ease', opacity: loading ? 0.7 : 1 }}
            >
              {loading ? 'Registering...' : 'Register Account'}
            </button>
          </form>
        </div>

        {/* Accounts list */}
        <div style={{ background: 'rgba(14,18,27,0.8)', backdropFilter: 'blur(24px)', border: '0.8px solid rgba(244,240,232,0.1)', borderRadius: 12, overflow: 'hidden' }}>
          <div style={{ padding: '20px 24px', borderBottom: '0.8px solid rgba(244,240,232,0.07)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase' as const, color: 'rgba(158,163,160,0.55)' }}>
              {accounts.length} SAVED ACCOUNTS
            </p>
          </div>

          {accounts.length === 0 ? (
            <div style={{ padding: 48, textAlign: 'center' as const }}>
              <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'rgba(158,163,160,0.35)', letterSpacing: '0.16em', textTransform: 'uppercase' as const }}>No cloud accounts registered</p>
            </div>
          ) : accounts.map((acc) => (
            <div key={acc.id} style={{ padding: '18px 24px', borderBottom: '0.8px solid rgba(244,240,232,0.05)', display: 'flex', alignItems: 'center', gap: 16, transition: 'background 150ms ease' }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(231,255,114,0.03)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            >
              {/* Provider icon */}
              <div style={{ width: 42, height: 42, background: 'rgba(255,255,255,0.06)', border: '0.8px solid rgba(244,240,232,0.1)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: '#E7FF72', flexShrink: 0 }}>
                {providerIcon[acc.provider] || '☁'}
              </div>

              <div style={{ flex: 1 }}>
                <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 15, fontWeight: 500, color: '#F4F0E8', marginBottom: 4 }}>{acc.name}</p>
                <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'rgba(158,163,160,0.55)', letterSpacing: '0.08em' }}>{providerLabel[acc.provider] || acc.provider.toUpperCase()}</p>
              </div>

              <div style={{ textAlign: 'right' as const }}>
                <span style={{ background: acc.is_active ? 'rgba(74,222,128,0.12)' : 'rgba(248,113,113,0.12)', color: acc.is_active ? '#4ade80' : '#f87171', border: `0.8px solid ${acc.is_active ? 'rgba(74,222,128,0.3)' : 'rgba(248,113,113,0.3)'}`, borderRadius: 6, padding: '3px 10px', fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.14em', fontWeight: 600 }}>
                  {acc.is_active ? 'ACTIVE' : 'INACTIVE'}
                </span>
                <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, color: 'rgba(158,163,160,0.4)', marginTop: 6, letterSpacing: '0.06em' }}>{acc.id.substring(0, 14)}…</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { CircularProgress, Box } from '@mui/material';
import { Plus } from 'lucide-react';
import { api } from '../../services/api';
import { useToast } from '../common/ToastContext';

interface Scan {
  id: string;
  cloud_account_id: string;
  status: string;
  progress: number;
  vulnerabilities_found: number;
  created_at: string;
}

interface CloudAccount {
  id: string;
  name: string;
  provider: string;
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const map: Record<string, { bg: string; color: string }> = {
    DEMO_COMPLETED: { bg: 'rgba(251,191,36,0.12)', color: 'var(--sev-medium)' },
    COMPLETED: { bg: 'rgba(231,255,114,0.12)', color: 'var(--nexus-accent-text)' },
    RUNNING: { bg: 'rgba(6,182,212,0.12)', color: 'var(--nexus-cyan-text)' },
    PENDING: { bg: 'rgba(251,191,36,0.12)', color: 'var(--sev-medium)' },
    FAILED: { bg: 'rgba(248,113,113,0.12)', color: 'var(--sev-critical)' },
  };
  const s = map[status] || { bg: 'var(--nexus-elevated-bg)', color: 'var(--nexus-text-muted)' };
  return (
    <span style={{ background: s.bg, color: s.color, border: `0.8px solid ${s.color}40`, borderRadius: 6, padding: '2px 8px', fontFamily: '"Geist Mono", monospace', fontSize: 10, letterSpacing: '0.1em', fontWeight: 600 }}>
      {status}
    </span>
  );
};

const ProgressBar: React.FC<{ value: number }> = ({ value }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
    <div style={{ flex: 1, height: 4, background: 'var(--nexus-elevated-bg)', borderRadius: 4, overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${value}%`, background: value === 100 ? '#E7FF72' : '#06B6D4', borderRadius: 4, transition: 'width 500ms ease' }} />
    </div>
    <span style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'var(--nexus-text-muted)', minWidth: 32 }}>{Math.round(value)}%</span>
  </div>
);

export const ScanList: React.FC = () => {
  const { showToast } = useToast();
  const [scans, setScans] = useState<Scan[]>([]);
  const [accounts, setAccounts] = useState<CloudAccount[]>([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchScans, 4000);
    return () => clearInterval(interval);
  }, []);

  const fetchAll = async () => {
    await Promise.all([fetchScans(), fetchAccounts()]);
    setPageLoading(false);
  };

  const fetchScans = async () => {
    try {
      const res = await api.get('/scans');
      setScans(res.data);
    } catch (err) { console.error(err); }
  };

  const fetchAccounts = async () => {
    try {
      const res = await api.get('/scans/cloud-accounts');
      setAccounts(res.data);
    } catch (err) { console.error(err); }
  };

  const triggerScan = async () => {
    if (!selectedAccount) return;
    setLoading(true);
    try {
      await api.post('/scans', { cloud_account_id: selectedAccount });
      setShowModal(false);
      showToast('Scan started — results will appear as the scan progresses.', 'success');
      fetchScans();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to trigger scan.', 'error');
    } finally {
      setLoading(false);
    }
  };

  if (pageLoading) return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
      <CircularProgress size={40} sx={{ color: 'var(--nexus-accent-bar)' }} />
    </Box>
  );

  return (
    <div className="scan-page" style={{ padding: '32px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <div className="scan-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.28em', textTransform: 'uppercase' as const, color: 'var(--nexus-text-muted)', marginBottom: 8 }}>CLOUD INFRASTRUCTURE</p>
          <h1 style={{ fontFamily: '"Geist", sans-serif', fontSize: 32, fontWeight: 500, letterSpacing: '-0.04em', color: 'var(--nexus-text-primary)', margin: 0 }}>Compliance Scans</h1>
        </div>
        <button
          onClick={() => setShowModal(true)}
          style={{ background: '#E7FF72', color: '#080b12', border: 'none', borderRadius: 10, padding: '11px 22px', fontSize: 12, fontWeight: 700, fontFamily: '"Geist Mono", monospace', letterSpacing: '0.14em', textTransform: 'uppercase' as const, cursor: 'pointer', transition: 'all 150ms ease', display: 'flex', alignItems: 'center', gap: 8 }}
          onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 6px 20px rgba(231,255,114,0.35)'}
          onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}
        >
          <Plus size={14} strokeWidth={2.5} />
          Trigger Scan
        </button>
      </div>

      <p role="note" style={{ color: 'var(--nexus-text-body)', lineHeight: 1.7, fontSize: 13, marginBottom: 20 }}>Demo results are sample data, never a verified cloud assessment. Failed scans have no complete result. A completed scan covers only the implemented checks, not a full compliance audit.</p>
      {/* Scans Table */}
      <div style={{ background: 'var(--nexus-surface)', backdropFilter: 'blur(24px)', border: '0.8px solid var(--nexus-border)', borderRadius: 12, overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '0.8px solid var(--nexus-border-soft)' }}>
              {['Scan ID', 'Cloud Account', 'Status', 'Progress', 'Findings', 'Triggered At'].map((h) => (
                <th key={h} style={{ padding: '14px 20px', textAlign: 'left' as const, fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase' as const, color: 'var(--nexus-text-faint)', fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {scans.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '48px', textAlign: 'center' as const, fontFamily: '"Geist Mono", monospace', fontSize: 11, letterSpacing: '0.14em', color: 'var(--nexus-text-dim)', textTransform: 'uppercase' as const }}>
                  No scans found - trigger your first scan to begin posture analysis
                </td>
              </tr>
            ) : scans.map((scan) => (
              <tr key={scan.id} style={{ borderBottom: '0.8px solid var(--nexus-border-soft)', transition: 'background 150ms ease' }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(231,255,114,0.03)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <td style={{ padding: '16px 20px', fontFamily: '"Geist Mono", monospace', fontSize: 11, color: 'var(--nexus-text-secondary)' }}>
                  {scan.id.substring(0, 12)}…
                </td>
                <td style={{ padding: '16px 20px', fontFamily: '"Geist Mono", monospace', fontSize: 11, color: 'var(--nexus-text-secondary)' }}>
                  {scan.cloud_account_id.substring(0, 10)}…
                </td>
                <td style={{ padding: '16px 20px' }}>
                  <StatusBadge status={scan.status} />
                </td>
                <td style={{ padding: '16px 20px', minWidth: 160 }}>
                  <ProgressBar value={scan.progress} />
                </td>
                <td style={{ padding: '16px 20px' }}>
                  <span style={{ fontFamily: '"Geist", sans-serif', fontSize: 20, fontWeight: 600, letterSpacing: '-0.02em', color: scan.vulnerabilities_found > 0 ? 'var(--sev-high)' : 'var(--sev-low)' }}>
                    {scan.status === 'COMPLETED' || scan.status === 'DEMO_COMPLETED' ? scan.vulnerabilities_found : '-'}
                  </span>
                </td>
                <td style={{ padding: '16px 20px', fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'var(--nexus-text-faint)' }}>
                  {new Date(scan.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'var(--nexus-overlay)', backdropFilter: 'blur(8px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'var(--nexus-surface-strong)', border: '0.8px solid var(--nexus-border-strong)', borderRadius: 16, padding: 24, width: 400, maxWidth: 'calc(100vw - 28px)', boxSizing: 'border-box', maxHeight: '90vh', overflowY: 'auto', boxShadow: 'rgba(0,0,0,0.6) 0px 24px 80px' }}>
            <h2 style={{ fontFamily: '"Geist", sans-serif', fontSize: 22, fontWeight: 500, letterSpacing: '-0.03em', color: 'var(--nexus-text-primary)', marginBottom: 6 }}>Start Cloud Scan</h2>
            <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'var(--nexus-text-muted)', letterSpacing: '0.1em', marginBottom: 28 }}>SELECT TARGET CLOUD ACCOUNT</p>

            <label style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase' as const, color: 'var(--nexus-text-muted)', display: 'block', marginBottom: 8 }}>Cloud Account</label>
            <select
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              style={{ width: '100%', background: 'var(--nexus-input-bg)', border: '0.8px solid var(--nexus-border-strong)', borderRadius: 10, padding: '11px 14px', fontSize: 13, fontFamily: '"Geist", sans-serif', color: 'var(--nexus-text-primary)', outline: 'none', marginBottom: 28, cursor: 'pointer' }}
            >
              <option value="" style={{ background: 'var(--nexus-surface-solid)' }}>Select account...</option>
              {accounts.map((acc) => (
                <option key={acc.id} value={acc.id} style={{ background: 'var(--nexus-surface-solid)' }}>
                  {acc.name} - {acc.provider.toUpperCase()}
                </option>
              ))}
            </select>

            <div style={{ display: 'flex', gap: 12 }}>
              <button
                onClick={() => setShowModal(false)}
                style={{ flex: 1, background: 'transparent', border: '0.8px solid var(--nexus-border-strong)', borderRadius: 10, padding: '11px 20px', color: 'var(--nexus-text-muted)', fontSize: 12, fontFamily: '"Geist", sans-serif', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={triggerScan}
                disabled={loading || !selectedAccount}
                style={{ flex: 1, background: selectedAccount ? '#E7FF72' : 'rgba(231,255,114,0.3)', color: '#080b12', border: 'none', borderRadius: 10, padding: '11px 20px', fontSize: 12, fontWeight: 700, fontFamily: '"Geist Mono", monospace', letterSpacing: '0.12em', cursor: selectedAccount ? 'pointer' : 'not-allowed', textTransform: 'uppercase' as const }}
              >
                {loading ? 'Launching...' : 'Execute'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

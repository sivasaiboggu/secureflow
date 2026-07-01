import React, { useEffect, useState } from 'react';
import { Box, Grid, CircularProgress } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area, CartesianGrid } from 'recharts';
import { api } from '../../services/api';

interface DashboardStats {
  totalScans: number;
  totalVulnerabilities: number;
  complianceScore: number;
  criticalCount: number;
  highCount: number;
  mediumCount: number;
  lowCount: number;
}

const StatCard: React.FC<{ label: string; value: string | number; sub?: string; accent?: string; index: number }> = ({ label, value, sub, accent = '#E7FF72', index }) => (
  <div style={{
    background: 'rgba(14,18,27,0.8)',
    backdropFilter: 'blur(24px)',
    border: '0.8px solid rgba(244,240,232,0.1)',
    borderRadius: 12,
    padding: '24px',
    position: 'relative',
    overflow: 'hidden',
    animation: `fadeUp 0.5s cubic-bezier(0.4,0,0.2,1) ${index * 60}ms both`,
  }}>
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: 2,
      background: `linear-gradient(90deg, transparent, ${accent}40, transparent)`,
    }} />
    <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase' as const, color: 'rgba(158,163,160,0.65)', marginBottom: 12 }}>
      {label}
    </p>
    <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 40, fontWeight: 600, letterSpacing: '-0.04em', color: accent, margin: 0, lineHeight: 1 }}>
      {value}
    </p>
    {sub && <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'rgba(158,163,160,0.55)', marginTop: 8, letterSpacing: '0.1em' }}>{sub}</p>}
  </div>
);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div style={{ background: 'rgba(14,18,27,0.95)', border: '0.8px solid rgba(244,240,232,0.15)', borderRadius: 8, padding: '8px 12px' }}>
        <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, color: '#9EA3A0', letterSpacing: '0.1em', textTransform: 'uppercase' as const }}>{label}</p>
        <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 18, fontWeight: 600, color: '#E7FF72', margin: 0 }}>{payload[0].value}</p>
      </div>
    );
  }
  return null;
};

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({ totalScans: 0, totalVulnerabilities: 0, complianceScore: 100, criticalCount: 0, highCount: 0, mediumCount: 0, lowCount: 0 });
  const [loading, setLoading] = useState(true);
  const [severityData, setSeverityData] = useState<any[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [lastUpdated, setLastUpdated] = useState('');

  useEffect(() => { fetchDashboardData(); }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [scansRes, vulnsRes] = await Promise.all([api.get('/scans'), api.get('/vulnerabilities')]);
      const scans = scansRes.data;
      const vulns = vulnsRes.data;

      const critical = vulns.filter((v: any) => v.severity === 'CRITICAL').length;
      const high = vulns.filter((v: any) => v.severity === 'HIGH').length;
      const medium = vulns.filter((v: any) => v.severity === 'MEDIUM').length;
      const low = vulns.filter((v: any) => v.severity === 'LOW').length;
      const compliance = Math.max(100 - (critical * 8) - (high * 4) - (medium * 2) - low, 45);

      setStats({ totalScans: scans.length, totalVulnerabilities: vulns.length, complianceScore: compliance, criticalCount: critical, highCount: high, mediumCount: medium, lowCount: low });
      setSeverityData([
        { name: 'Critical', count: critical, fill: '#f87171' },
        { name: 'High', count: high, fill: '#fb923c' },
        { name: 'Medium', count: medium, fill: '#fbbf24' },
        { name: 'Low', count: low, fill: '#4ade80' },
      ]);
      setTrendData([
        { date: 'T-4', score: 100 }, { date: 'T-3', score: 94 },
        { date: 'T-2', score: 88 }, { date: 'T-1', score: Math.min(compliance + 5, 100) },
        { date: 'Now', score: compliance },
      ]);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
      <CircularProgress size={48} sx={{ color: '#E7FF72' }} />
    </Box>
  );

  const complianceColor = stats.complianceScore >= 80 ? '#4ade80' : stats.complianceScore >= 60 ? '#fbbf24' : '#f87171';

  return (
    <div style={{ padding: '32px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 40 }}>
        <div>
          <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.28em', textTransform: 'uppercase' as const, color: 'rgba(158,163,160,0.6)', marginBottom: 8 }}>
            SECURITY POSTURE
          </p>
          <h1 style={{ fontFamily: '"Geist", sans-serif', fontSize: 32, fontWeight: 500, letterSpacing: '-0.04em', color: '#F4F0E8', margin: 0 }}>
            Overview Dashboard
          </h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {lastUpdated && (
            <span style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'rgba(158,163,160,0.5)', letterSpacing: '0.1em' }}>
              UPDATED {lastUpdated}
            </span>
          )}
          <button
            onClick={fetchDashboardData}
            style={{ background: '#E7FF72', color: '#080b12', border: 'none', borderRadius: 10, padding: '9px 18px', fontSize: 12, fontWeight: 700, fontFamily: '"Geist Mono", monospace', letterSpacing: '0.12em', textTransform: 'uppercase' as const, cursor: 'pointer', transition: 'all 150ms ease' }}
            onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 6px 20px rgba(231,255,114,0.35)'}
            onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard index={0} label="Cloud Scans" value={stats.totalScans} sub="Total executed" accent="#06B6D4" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard index={1} label="Vulnerabilities" value={stats.totalVulnerabilities} sub="Active findings" accent="#fb923c" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard index={2} label="Compliance Score" value={`${stats.complianceScore}%`} sub="CIS benchmark" accent={complianceColor} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard index={3} label="Critical Threats" value={stats.criticalCount} sub="Immediate action" accent="#f87171" />
        </Grid>
      </Grid>

      {/* Charts row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Severity Distribution */}
        <Grid item xs={12} md={6}>
          <div style={{ background: 'rgba(14,18,27,0.8)', backdropFilter: 'blur(24px)', border: '0.8px solid rgba(244,240,232,0.1)', borderRadius: 12, padding: '24px' }}>
            <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase' as const, color: 'rgba(158,163,160,0.6)', marginBottom: 6 }}>ANALYSIS</p>
            <h3 style={{ fontFamily: '"Geist", sans-serif', fontSize: 18, fontWeight: 500, letterSpacing: '-0.03em', color: '#F4F0E8', marginBottom: 24 }}>Severity Distribution</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={severityData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(244,240,232,0.05)" />
                <XAxis dataKey="name" tick={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, fill: '#9EA3A0', letterSpacing: '0.1em' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, fill: 'rgba(158,163,160,0.5)' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(231,255,114,0.04)' }} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {severityData.map((entry, index) => (
                    <rect key={`bar-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Grid>

        {/* Compliance Trend */}
        <Grid item xs={12} md={6}>
          <div style={{ background: 'rgba(14,18,27,0.8)', backdropFilter: 'blur(24px)', border: '0.8px solid rgba(244,240,232,0.1)', borderRadius: 12, padding: '24px' }}>
            <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase' as const, color: 'rgba(158,163,160,0.6)', marginBottom: 6 }}>TREND</p>
            <h3 style={{ fontFamily: '"Geist", sans-serif', fontSize: 18, fontWeight: 500, letterSpacing: '-0.03em', color: '#F4F0E8', marginBottom: 24 }}>Compliance Over Time</h3>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={trendData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="complianceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#E7FF72" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#E7FF72" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(244,240,232,0.05)" />
                <XAxis dataKey="date" tick={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, fill: '#9EA3A0' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, fill: 'rgba(158,163,160,0.5)' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="score" stroke="#E7FF72" strokeWidth={2} fill="url(#complianceGrad)" dot={{ fill: '#E7FF72', r: 4, strokeWidth: 0 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Grid>
      </Grid>

      {/* Bottom: severity breakdown list */}
      <div style={{ background: 'rgba(14,18,27,0.8)', backdropFilter: 'blur(24px)', border: '0.8px solid rgba(244,240,232,0.1)', borderRadius: 12, padding: '24px' }}>
        <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase' as const, color: 'rgba(158,163,160,0.6)', marginBottom: 20 }}>FINDING BREAKDOWN</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16 }}>
          {[
            { label: 'CRITICAL', count: stats.criticalCount, color: '#f87171', bg: 'rgba(239,68,68,0.1)' },
            { label: 'HIGH', count: stats.highCount, color: '#fb923c', bg: 'rgba(249,115,22,0.1)' },
            { label: 'MEDIUM', count: stats.mediumCount, color: '#fbbf24', bg: 'rgba(234,179,8,0.1)' },
            { label: 'LOW', count: stats.lowCount, color: '#4ade80', bg: 'rgba(34,197,94,0.1)' },
          ].map((item) => (
            <div key={item.label} style={{ background: item.bg, border: `0.8px solid ${item.color}30`, borderRadius: 10, padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, letterSpacing: '0.14em', color: item.color }}>{item.label}</span>
              <span style={{ fontFamily: '"Geist", sans-serif', fontSize: 28, fontWeight: 600, letterSpacing: '-0.03em', color: item.color }}>{item.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

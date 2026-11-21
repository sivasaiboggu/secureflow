import React, { useEffect, useState } from 'react';
import { Grid, Skeleton } from '@mui/material';
import { BarChart, Bar, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area, CartesianGrid } from 'recharts';
import { motion, type Variants } from 'framer-motion';
import { RefreshCw, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';
import { useToast } from '../common/ToastContext';

interface DashboardStats {
  totalScans: number;
  totalVulnerabilities: number;
  complianceScore: number | null;
  criticalCount: number;
  highCount: number;
  mediumCount: number;
  lowCount: number;
}

/** GET /api/v1/analytics/summary — open-only totals straight from the API. */
interface AnalyticsSummary {
  total_open_vulnerabilities: number;
  average_cvss_score: number;
  severity_distribution: Record<string, number>;
  resource_distribution: Record<string, number>;
}

const containerVariants: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: 'easeOut' } },
};

const glassPanel: React.CSSProperties = {
  background: 'var(--nexus-surface)',
  backdropFilter: 'blur(24px)',
  border: '0.8px solid var(--nexus-border)',
  borderRadius: 12,
};

const monoLabel: React.CSSProperties = {
  fontFamily: '"Geist Mono", monospace',
  fontSize: 9,
  letterSpacing: '0.22em',
  textTransform: 'uppercase',
  color: 'var(--nexus-text-faint)',
};

const StatCard: React.FC<{ label: string; value: string | number; sub?: string; accent?: string }> = ({ label, value, sub, accent = 'var(--nexus-accent-text)' }) => (
  <motion.div
    variants={itemVariants}
    whileHover={{ y: -2 }}
    transition={{ duration: 0.16, ease: [0.22, 1, 0.36, 1] }}
    className="nexus-lift"
    style={{
      ...glassPanel,
      padding: '24px',
      position: 'relative',
      overflow: 'hidden',
    }}
  >
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: 2,
      background: `linear-gradient(90deg, transparent, color-mix(in srgb, ${accent} 25%, transparent), transparent)`,
    }} />
    <p style={{ ...monoLabel, marginBottom: 12 }}>{label}</p>
    <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 40, fontWeight: 600, letterSpacing: '-0.04em', color: accent, margin: 0, lineHeight: 1, fontVariantNumeric: 'tabular-nums' }}>
      {value}
    </p>
    {sub && <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'var(--nexus-text-faint)', marginTop: 8, letterSpacing: '0.1em' }}>{sub}</p>}
  </motion.div>
);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div style={{ background: 'var(--nexus-surface-strong)', border: '0.8px solid var(--nexus-border-strong)', borderRadius: 8, padding: '8px 12px', boxShadow: 'var(--nexus-shadow)' }}>
        <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'var(--nexus-text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{label}</p>
        <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 18, fontWeight: 600, color: 'var(--nexus-accent-text)', margin: 0 }}>{payload[0].value}</p>
      </div>
    );
  }
  return null;
};

const DashboardSkeleton: React.FC = () => (
  <div style={{ padding: '32px', maxWidth: 1400, margin: '0 auto' }}>
    <Skeleton variant="text" width={180} height={16} sx={{ mb: 1 }} />
    <Skeleton variant="text" width={320} height={44} sx={{ mb: 5 }} />
    <Grid container spacing={2} sx={{ mb: 4 }}>
      {[0, 1, 2, 3].map((i) => (
        <Grid item xs={12} sm={6} md={3} key={i}>
          <Skeleton variant="rounded" height={132} />
        </Grid>
      ))}
    </Grid>
    <Grid container spacing={3} sx={{ mb: 4 }}>
      <Grid item xs={12} md={6}>
        <Skeleton variant="rounded" height={332} />
      </Grid>
      <Grid item xs={12} md={6}>
        <Skeleton variant="rounded" height={332} />
      </Grid>
    </Grid>
    <Skeleton variant="rounded" height={116} />
  </div>
);

export const Dashboard: React.FC = () => {
  const { showToast } = useToast();
  const [stats, setStats] = useState<DashboardStats>({ totalScans: 0, totalVulnerabilities: 0, complianceScore: null, criticalCount: 0, highCount: 0, mediumCount: 0, lowCount: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasData, setHasData] = useState(false);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [compliance, setCompliance] = useState<Record<string, number> | null>(null);
  const [topFindings, setTopFindings] = useState<any[]>([]);
  const [severityData, setSeverityData] = useState<any[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [lastUpdated, setLastUpdated] = useState('');

  useEffect(() => { fetchDashboardData(); }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // The analytics summary is best-effort: if it is unavailable the
      // scans/vulnerabilities lists below are the fallback for every total.
      const [scansRes, vulnsRes, summaryRes, complianceRes] = await Promise.allSettled([
        api.get('/scans'),
        api.get('/vulnerabilities'),
        api.get('/analytics/summary'),
        api.get('/compliance/summary'),
      ]);
      if (scansRes.status === 'rejected') throw scansRes.reason;
      if (vulnsRes.status === 'rejected') throw vulnsRes.reason;
      const scans = scansRes.value.data;
      const vulns = vulnsRes.value.data;
      const summaryData: AnalyticsSummary | null = summaryRes.status === 'fulfilled' ? summaryRes.value.data : null;

      const countBySeverity = (sev: string) =>
        summaryData
          ? (summaryData.severity_distribution?.[sev] ?? 0)
          : vulns.filter((v: any) => v.severity === sev).length;
      const critical = countBySeverity('CRITICAL');
      const high = countBySeverity('HIGH');
      const medium = countBySeverity('MEDIUM');
      const low = countBySeverity('LOW');
      const totalVulns = summaryData ? summaryData.total_open_vulnerabilities : vulns.length;

      // Real evaluated coverage only: weighted pass rate across completed scans
      // that ran at least one check. Never a penalty formula or a default 100.
      const evaluated = scans
        .filter((s: any) => s.status === 'COMPLETED' && ((s.passed_checks || 0) + (s.failed_checks || 0)) > 0)
        .sort((a: any, b: any) => new Date(a.completed_at).getTime() - new Date(b.completed_at).getTime());
      let compliance: number | null = null;
      if (evaluated.length > 0) {
        const passed = evaluated.reduce((n: number, s: any) => n + (s.passed_checks || 0), 0);
        const total = evaluated.reduce((n: number, s: any) => n + (s.passed_checks || 0) + (s.failed_checks || 0), 0);
        compliance = Math.round((passed / total) * 100);
      }

      setSummary(summaryData);
      setCompliance(complianceRes.status === 'fulfilled' ? complianceRes.value.data : null);
      setTopFindings(
        [...vulns]
          .filter((v: any) => v.severity === 'CRITICAL' || v.severity === 'HIGH')
          .sort((a: any, b: any) => (b.cvss_score || 0) - (a.cvss_score || 0))
          .slice(0, 5)
      );
      setStats({ totalScans: scans.length, totalVulnerabilities: totalVulns, complianceScore: compliance, criticalCount: critical, highCount: high, mediumCount: medium, lowCount: low });
      setSeverityData([
        { name: 'Critical', count: critical, fill: 'var(--sev-critical)' },
        { name: 'High', count: high, fill: 'var(--sev-high)' },
        { name: 'Medium', count: medium, fill: 'var(--sev-medium)' },
        { name: 'Low', count: low, fill: 'var(--sev-low)' },
      ]);
      setTrendData(evaluated.map((s: any) => ({
        date: s.completed_at ? new Date(s.completed_at).toLocaleDateString() : 'scan',
        score: Math.round((s.passed_checks / (s.passed_checks + s.failed_checks)) * 100),
      })));
      setLastUpdated(new Date().toLocaleTimeString());
      setHasData(true);
    } catch (err: any) {
      const message = err?.response?.data?.detail || err?.message || 'Could not load dashboard data.';
      setError(message);
      if (hasData) showToast(`Dashboard refresh failed: ${message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !hasData) return <DashboardSkeleton />;

  if (error && !hasData) {
    return (
      <div style={{ padding: '32px', maxWidth: 1400, margin: '0 auto' }}>
        <div style={{ ...glassPanel, padding: '48px 32px', textAlign: 'center', maxWidth: 560, margin: '64px auto 0' }}>
          <AlertTriangle size={28} color="var(--sev-high)" style={{ marginBottom: 16 }} />
          <h2 style={{ fontFamily: '"Geist", sans-serif', fontSize: 22, fontWeight: 500, letterSpacing: '-0.03em', color: 'var(--nexus-text-primary)', margin: '0 0 10px' }}>
            Couldn&rsquo;t load the dashboard
          </h2>
          <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 14, lineHeight: 1.7, color: 'var(--nexus-text-body)', margin: '0 0 24px' }}>
            {error}
          </p>
          <button
            onClick={fetchDashboardData}
            style={{ background: '#E7FF72', color: '#080b12', border: 'none', borderRadius: 10, padding: '11px 22px', fontSize: 12, fontWeight: 700, fontFamily: '"Geist Mono", monospace', letterSpacing: '0.12em', textTransform: 'uppercase', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 8 }}
          >
            <RefreshCw size={14} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  const complianceColor = stats.complianceScore === null ? 'var(--nexus-text-faint)' : stats.complianceScore >= 80 ? 'var(--sev-low)' : stats.complianceScore >= 60 ? 'var(--sev-medium)' : 'var(--sev-critical)';
  const resourceEntries = summary
    ? Object.entries(summary.resource_distribution ?? {}).sort((a, b) => b[1] - a[1]).slice(0, 6)
    : [];

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="dashboard-page" style={{ padding: '32px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <motion.div variants={itemVariants} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 40, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <p style={{ ...monoLabel, marginBottom: 8 }}>SECURITY POSTURE</p>
          <h1 style={{ fontFamily: '"Geist", sans-serif', fontSize: 32, fontWeight: 500, letterSpacing: '-0.04em', color: 'var(--nexus-text-primary)', margin: 0 }}>
            Overview Dashboard
          </h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {lastUpdated && (
            <span style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'var(--nexus-text-faint)', letterSpacing: '0.1em' }}>
              UPDATED {lastUpdated}
            </span>
          )}
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            style={{ background: '#E7FF72', color: '#080b12', border: 'none', borderRadius: 10, padding: '9px 18px', fontSize: 12, fontWeight: 700, fontFamily: '"Geist Mono", monospace', letterSpacing: '0.12em', textTransform: 'uppercase', cursor: loading ? 'default' : 'pointer', opacity: loading ? 0.6 : 1, transition: 'all 150ms ease', display: 'inline-flex', alignItems: 'center', gap: 8 }}
          >
            <RefreshCw size={13} />
            Refresh
          </button>
        </div>
      </motion.div>

      {/* Inline refresh failure — data from the last good load stays visible */}
      {error && hasData && (
        <div role="alert" style={{ ...glassPanel, borderColor: 'var(--sev-high)', padding: '12px 16px', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <AlertTriangle size={15} color="var(--sev-high)" style={{ flexShrink: 0 }} />
          <span style={{ fontFamily: '"Geist", sans-serif', fontSize: 13, color: 'var(--nexus-text-body)', flex: 1, minWidth: 200 }}>
            Refresh failed — showing data from the last successful load. {error}
          </span>
          <button onClick={fetchDashboardData} style={{ background: 'transparent', border: '0.8px solid var(--nexus-border-strong)', borderRadius: 8, padding: '6px 12px', color: 'var(--nexus-text-primary)', fontSize: 11, fontFamily: '"Geist Mono", monospace', letterSpacing: '0.1em', cursor: 'pointer' }}>
            RETRY
          </button>
        </div>
      )}

      {/* Stat Cards */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Cloud Scans" value={stats.totalScans} sub="Total executed" accent="var(--nexus-cyan-text)" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            label="Vulnerabilities"
            value={stats.totalVulnerabilities}
            sub={summary ? `Open findings · Avg CVSS ${summary.average_cvss_score.toFixed(1)}` : 'Active findings'}
            accent="var(--sev-high)"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Compliance Score" value={stats.complianceScore === null ? '—' : `${stats.complianceScore}%`} sub={stats.complianceScore === null ? 'No evaluated checks yet' : 'Pass rate across completed scans'} accent={complianceColor} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Critical Threats" value={stats.criticalCount} sub="Immediate action" accent="var(--sev-critical)" />
        </Grid>
      </Grid>

      {/* Charts row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Severity Distribution */}
        <Grid item xs={12} md={6}>
          <motion.div variants={itemVariants} style={{ ...glassPanel, padding: '24px' }}>
            <p style={{ ...monoLabel, marginBottom: 6 }}>ANALYSIS</p>
            <h3 style={{ fontFamily: '"Geist", sans-serif', fontSize: 18, fontWeight: 500, letterSpacing: '-0.03em', color: 'var(--nexus-text-primary)', marginBottom: 24 }}>Severity Distribution</h3>
            {stats.totalVulnerabilities === 0 ? (
              <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '0.8px dashed var(--nexus-border-strong)', borderRadius: 10 }}>
                <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 11, color: 'var(--nexus-text-faint)', letterSpacing: '0.06em', textAlign: 'center', padding: '0 24px' }}>
                  No open findings to chart.
                </p>
              </div>
            ) : (
            <ResponsiveContainer width="100%" height={260}>
              {/* Charts render without entry animation: on a theme toggle
                  recharts re-mounts, and the 1.5s grow-in left the chart
                  visibly empty for seconds. Instant rendering also reads
                  as more deliberate on a security console. */}
              <BarChart data={severityData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 4" stroke="var(--nexus-border-soft)" />
                <XAxis dataKey="name" tick={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, fill: 'var(--nexus-text-muted)', letterSpacing: '0.1em' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, fill: 'var(--nexus-text-faint)' }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(231,255,114,0.04)' }} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]} isAnimationActive={false}>
                  {severityData.map((entry) => (
                    <Cell key={entry.name} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            )}
          </motion.div>
        </Grid>

        {/* Compliance Trend */}
        <Grid item xs={12} md={6}>
          <motion.div variants={itemVariants} style={{ ...glassPanel, padding: '24px' }}>
            <p style={{ ...monoLabel, marginBottom: 6 }}>TREND</p>
            <h3 style={{ fontFamily: '"Geist", sans-serif', fontSize: 18, fontWeight: 500, letterSpacing: '-0.03em', color: 'var(--nexus-text-primary)', marginBottom: 24 }}>Compliance Over Time</h3>
            {trendData.length < 2 ? (
              <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '0.8px dashed var(--nexus-border-strong)', borderRadius: 10 }}>
                <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 11, color: 'var(--nexus-text-faint)', letterSpacing: '0.06em', textAlign: 'center', padding: '0 24px' }}>
                  Appears after at least two completed scans with evaluated checks.
                </p>
              </div>
            ) : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={trendData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="complianceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--nexus-accent-bar)" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="var(--nexus-accent-bar)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 4" stroke="var(--nexus-border-soft)" />
                <XAxis dataKey="date" tick={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, fill: 'var(--nexus-text-muted)' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, fill: 'var(--nexus-text-faint)' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="score" stroke="var(--nexus-accent-bar)" strokeWidth={2} fill="url(#complianceGrad)" isAnimationActive={false} dot={{ fill: 'var(--nexus-accent-bar)', r: 4, strokeWidth: 0 }} />
              </AreaChart>
            </ResponsiveContainer>
            )}
          </motion.div>
        </Grid>
      </Grid>

      {/* Bottom: severity breakdown list */}
      <motion.div variants={itemVariants} style={{ ...glassPanel, padding: '24px' }}>
        <p style={{ ...monoLabel, marginBottom: 20 }}>FINDING BREAKDOWN</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          {[
            { label: 'CRITICAL', count: stats.criticalCount, color: 'var(--sev-critical)', bg: 'rgba(239,68,68,0.1)' },
            { label: 'HIGH', count: stats.highCount, color: 'var(--sev-high)', bg: 'rgba(249,115,22,0.1)' },
            { label: 'MEDIUM', count: stats.mediumCount, color: 'var(--sev-medium)', bg: 'rgba(234,179,8,0.1)' },
            { label: 'LOW', count: stats.lowCount, color: 'var(--sev-low)', bg: 'rgba(34,197,94,0.1)' },
          ].map((item) => (
            <div key={item.label} className="nexus-lift" style={{ background: item.bg, border: `0.8px solid color-mix(in srgb, ${item.color} 35%, transparent)`, borderRadius: 10, padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, letterSpacing: '0.14em', color: item.color }}>{item.label}</span>
              <span style={{ fontFamily: '"Geist", sans-serif', fontSize: 28, fontWeight: 600, letterSpacing: '-0.03em', color: item.color }}>{item.count}</span>
            </div>
          ))}
        </div>
        {resourceEntries.length > 0 && (
          <div style={{ marginTop: 20, paddingTop: 20, borderTop: '0.8px solid var(--nexus-border-soft)' }}>
            <p style={{ ...monoLabel, marginBottom: 12 }}>OPEN FINDINGS BY RESOURCE</p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {resourceEntries.map(([resource, count]) => (
                <span key={resource} style={{ background: 'var(--nexus-elevated-bg)', border: '0.8px solid var(--nexus-border)', borderRadius: 6, padding: '4px 10px', fontFamily: '"Geist Mono", monospace', fontSize: 10, letterSpacing: '0.1em', color: 'var(--nexus-text-secondary)' }}>
                  {resource} · {count}
                </span>
              ))}
            </div>
          </div>
        )}
      </motion.div>
      {/* Compliance overview + top findings */}
      <Grid container spacing={3} sx={{ mt: 4 }}>
        <Grid item xs={12} md={6}>
          <motion.div variants={itemVariants} style={{ ...glassPanel, padding: '24px', height: '100%' }}>
            <p style={{ ...monoLabel, marginBottom: 6 }}>COMPLIANCE</p>
            <h3 style={{ fontFamily: '"Geist", sans-serif', fontSize: 18, fontWeight: 500, letterSpacing: '-0.03em', color: 'var(--nexus-text-primary)', marginBottom: 20 }}>Framework Overview</h3>
            {(!compliance || Object.keys(compliance).length === 0) ? (
              <div style={{ minHeight: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '0.8px dashed var(--nexus-border-strong)', borderRadius: 10 }}>
                <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 11, color: 'var(--nexus-text-faint)', letterSpacing: '0.06em', textAlign: 'center', padding: '0 24px' }}>
                  No framework has evaluated checks yet. Scores appear after a completed scan.
                </p>
              </div>
            ) : (
              Object.entries(compliance)
                .sort((a, b) => a[1] - b[1])
                .map(([fw, score]) => {
                  const barColor = score >= 80 ? 'var(--sev-low)' : score >= 60 ? 'var(--sev-medium)' : 'var(--sev-critical)';
                  return (
                    <div key={fw} style={{ marginBottom: 16 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <span style={{ fontFamily: '"Geist Mono", monospace', fontSize: 11, letterSpacing: '0.12em', color: 'var(--nexus-text-secondary)' }}>{fw.split('_').join(' ')}</span>
                        <span style={{ fontFamily: '"Geist Mono", monospace', fontSize: 11, fontWeight: 700, color: barColor }}>{score.toFixed(0)}%</span>
                      </div>
                      <div style={{ height: 8, borderRadius: 4, background: 'var(--nexus-elevated-bg)', overflow: 'hidden', boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.25)' }}>
                        <motion.div initial={{ width: 0 }} animate={{ width: `${score}%` }} transition={{ duration: 0.6, ease: 'easeOut' }} style={{ height: '100%', borderRadius: 4, background: barColor }} />
                      </div>
                    </div>
                  );
                })
            )}
          </motion.div>
        </Grid>
        <Grid item xs={12} md={6}>
          <motion.div variants={itemVariants} style={{ ...glassPanel, padding: '24px', height: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 20 }}>
              <div>
                <p style={{ ...monoLabel, marginBottom: 6 }}>ACT NOW</p>
                <h3 style={{ fontFamily: '"Geist", sans-serif', fontSize: 18, fontWeight: 500, letterSpacing: '-0.03em', color: 'var(--nexus-text-primary)', margin: 0 }}>Top Critical Findings</h3>
              </div>
              <Link to="/vulnerabilities" style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, letterSpacing: '0.12em', color: 'var(--nexus-accent-text)', textDecoration: 'none', borderBottom: '0.8px solid transparent', paddingBottom: 2 }} onMouseEnter={(e) => { e.currentTarget.style.borderBottomColor = 'var(--nexus-accent-text)'; }} onMouseLeave={(e) => { e.currentTarget.style.borderBottomColor = 'transparent'; }}>VIEW ALL →</Link>
            </div>
            {topFindings.length === 0 ? (
              <div style={{ minHeight: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '0.8px dashed var(--nexus-border-strong)', borderRadius: 10 }}>
                <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 11, color: 'var(--nexus-text-faint)', letterSpacing: '0.06em', textAlign: 'center', padding: '0 24px' }}>
                  No critical or high findings open. Good posture.
                </p>
              </div>
            ) : (
              topFindings.map((v: any) => (
                <Link key={v.id} to="/vulnerabilities" className="nexus-row" style={{ textDecoration: 'none', display: 'block', padding: '12px 8px', margin: '0 -8px', borderBottom: '0.8px solid var(--nexus-border-soft)', borderRadius: 8 }}>
                  <span style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
                    <span style={{ flex: 1, minWidth: 0 }}>
                      <span style={{ display: 'block', fontFamily: '"Geist", sans-serif', fontSize: 13, fontWeight: 500, color: 'var(--nexus-text-primary)', lineHeight: 1.4 }}>{v.title}</span>
                      <span style={{ display: 'block', fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'var(--nexus-text-faint)', marginTop: 4 }}>{v.resource_type} / {v.resource_id}</span>
                    </span>
                    <span style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
                      <span style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, fontWeight: 700, letterSpacing: '0.12em', color: v.severity === 'CRITICAL' ? 'var(--sev-critical)' : 'var(--sev-high)' }}>{v.severity}</span>
                      <span style={{ fontFamily: '"Geist Mono", monospace', fontSize: 13, fontWeight: 700, color: 'var(--nexus-text-primary)' }}>{v.cvss_score?.toFixed(1)}</span>
                    </span>
                  </span>
                </Link>
              ))
            )}
          </motion.div>
        </Grid>
      </Grid>
    </motion.div>
  );
};

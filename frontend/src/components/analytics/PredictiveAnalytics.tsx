import React, { useState } from 'react';
import { api } from '../../services/api';

export const PredictiveAnalytics: React.FC = () => {
  const [logText, setLogText] = useState('{"eventVersion":"1.08","userIdentity":{"type":"Root","arn":"arn:aws:iam::123456789:root"},"eventName":"DeleteBucketPolicy","requestParameters":{"bucketName":"prod-database-backups"}}');
  const [logResult, setLogResult] = useState<any>(null);
  const [logLoading, setLogLoading] = useState(false);

  const [metricsText, setMetricsText] = useState('0.85, 0.92, 0.44, 0.12, 0.76, 0.99, 0.05, 0.81');
  const [anomalyResult, setAnomalyResult] = useState<any>(null);
  const [anomalyLoading, setAnomalyLoading] = useState(false);

  const handleLogClassification = async () => {
    setLogLoading(true);
    setLogResult(null);
    try {
      const res = await api.post('/vulnerabilities/analyze-log', { log_payload: logText });
      setLogResult(res.data);
    } catch (err: any) {
      setLogResult({ error: err.response?.data?.detail || 'NLP inference failed.' });
    } finally { setLogLoading(false); }
  };

  const handleAnomalyDetection = async () => {
    setAnomalyLoading(true);
    setAnomalyResult(null);
    try {
      const parsed = metricsText.split(',').map(v => parseFloat(v.trim()));
      if (parsed.length !== 8 || parsed.some(isNaN)) {
        setAnomalyResult({ error: 'Please enter exactly 8 valid numeric values.' });
        return;
      }
      const res = await api.post('/vulnerabilities/analyze-metrics', { metrics: parsed });
      setAnomalyResult(res.data);
    } catch (err: any) {
      setAnomalyResult({ error: err.response?.data?.detail || 'Anomaly evaluation failed.' });
    } finally { setAnomalyLoading(false); }
  };

  const ResultCard: React.FC<{ data: any; type: 'log' | 'anomaly' }> = ({ data, type }) => {
    if (data.error) return (
      <div style={{ background: 'rgba(239,68,68,0.1)', border: '0.8px solid rgba(239,68,68,0.3)', borderRadius: 10, padding: '14px 18px' }}>
        <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 11, color: 'var(--sev-critical)', letterSpacing: '0.05em' }}>{data.error}</p>
      </div>
    );

    if (type === 'log') {
      const isThret = data.is_threat;
      return (
        <div style={{ background: isThret ? 'rgba(239,68,68,0.1)' : 'rgba(74,222,128,0.1)', border: `0.8px solid ${isThret ? 'rgba(239,68,68,0.3)' : 'rgba(74,222,128,0.3)'}`, borderRadius: 10, padding: '18px 20px' }}>
          <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, letterSpacing: '0.22em', color: isThret ? 'var(--sev-critical)' : 'var(--sev-low)', marginBottom: 8 }}>
            {isThret ? 'REVIEW FLAG' : 'NO RULE FLAG - NOT PROOF OF SAFETY'}
          </p>
          <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 15, fontWeight: 500, color: 'var(--nexus-text-primary)', marginBottom: 4 }}>
            {data.classification}
          </p>
          <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 11, color: 'var(--nexus-text-muted)' }}>
            Uncalibrated score: {Number.isFinite(data.confidence) ? data.confidence.toFixed(3) : 'unavailable'} · Method: {data.method || 'unspecified'}
          </p>
        </div>
      );
    }

    const isAnomaly = data.is_anomaly;
    return (
      <div style={{ background: isAnomaly ? 'rgba(251,191,36,0.1)' : 'rgba(74,222,128,0.1)', border: `0.8px solid ${isAnomaly ? 'rgba(251,191,36,0.3)' : 'rgba(74,222,128,0.3)'}`, borderRadius: 10, padding: '18px 20px' }}>
        <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, letterSpacing: '0.22em', color: isAnomaly ? 'var(--sev-medium)' : 'var(--sev-low)', marginBottom: 8 }}>
          {isAnomaly ? 'OUTLIER FLAG' : 'NO OUTLIER FLAG - VALIDATION REQUIRED'}
        </p>
        <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 15, fontWeight: 500, color: 'var(--nexus-text-primary)', marginBottom: 4 }}>
          Uncalibrated anomaly score: {data.anomaly_score?.toFixed(4)}
        </p>
        <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 11, color: 'var(--nexus-text-muted)' }}>
          ALGORITHM: {data.algorithm}
        </p>
      </div>
    );
  };

  return (
    <div style={{ padding: '32px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 40 }}>
        <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.28em', textTransform: 'uppercase' as const, color: 'var(--nexus-text-muted)', marginBottom: 8 }}>EXPERIMENTAL REVIEW TOOLS</p>
        <h1 style={{ fontFamily: '"Geist", sans-serif', fontSize: 32, fontWeight: 500, letterSpacing: '-0.04em', color: 'var(--nexus-text-primary)', margin: 0 }}>Log and metric review</h1>
        <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 14, color: 'var(--nexus-text-muted)', marginTop: 8 }}>Scanner severity uses CVSS rules. These separate review tools are experimental, not verified threat detection.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 360px), 1fr))', gap: 20 }}>
        {/* Panel 1: NLP Log Classifier */}
        <div style={{ background: 'var(--nexus-surface)', backdropFilter: 'blur(24px)', border: '0.8px solid var(--nexus-border)', borderRadius: 12, padding: 28, display: 'flex', flexDirection: 'column' as const, gap: 20 }}>
          <div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
              <span style={{ background: 'rgba(6,182,212,0.15)', color: 'var(--nexus-cyan-text)', border: '0.8px solid rgba(6,182,212,0.3)', borderRadius: 6, padding: '2px 8px', fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.14em' }}>NLP</span>
              <span style={{ background: 'rgba(231,255,114,0.12)', color: '#E7FF72', border: '0.8px solid rgba(231,255,114,0.25)', borderRadius: 6, padding: '2px 8px', fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.14em' }}>RULES / OPTIONAL MODEL</span>
            </div>
            <h2 style={{ fontFamily: '"Geist", sans-serif', fontSize: 20, fontWeight: 500, letterSpacing: '-0.03em', color: 'var(--nexus-text-primary)', margin: 0, marginBottom: 8 }}>CloudTrail Log Classifier</h2>
            <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 13, color: 'var(--nexus-text-muted)', lineHeight: 1.6, margin: 0 }}>
              Submit a CloudTrail event for heuristic review. An optional local model requires separate setup and validation; no fine-tuning accuracy is claimed.
            </p>
          </div>

          <div>
            <label style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase' as const, color: 'var(--nexus-text-muted)', display: 'block', marginBottom: 8 }}>JSON EVENT PAYLOAD</label>
            <textarea
              rows={7}
              value={logText}
              onChange={(e) => setLogText(e.target.value)}
              style={{ width: '100%', background: 'var(--nexus-code-bg)', border: '0.8px solid var(--nexus-border)', borderRadius: 10, padding: '12px 14px', fontSize: 12, fontFamily: '"Geist Mono", monospace', color: 'var(--nexus-code-text)', outline: 'none', resize: 'vertical' as const, lineHeight: 1.6, boxSizing: 'border-box' as const }}
              onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(6,182,212,0.4)'}
              onBlur={(e) => e.currentTarget.style.borderColor = 'var(--nexus-border)'}
            />
          </div>

          <button
            onClick={handleLogClassification}
            disabled={logLoading}
            style={{ background: logLoading ? 'rgba(6,182,212,0.3)' : '#06B6D4', color: '#080b12', border: 'none', borderRadius: 10, padding: '12px 20px', fontSize: 11, fontWeight: 700, fontFamily: '"Geist Mono", monospace', letterSpacing: '0.16em', textTransform: 'uppercase' as const, cursor: logLoading ? 'not-allowed' : 'pointer', transition: 'all 150ms ease' }}
          >
            {logLoading ? 'Analyzing...' : 'Run Log Classification →'}
          </button>

          {logResult && <ResultCard data={logResult} type="log" />}
        </div>

        {/* Panel 2: Anomaly Detection */}
        <div style={{ background: 'var(--nexus-surface)', backdropFilter: 'blur(24px)', border: '0.8px solid var(--nexus-border)', borderRadius: 12, padding: 28, display: 'flex', flexDirection: 'column' as const, gap: 20 }}>
          <div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
              <span style={{ background: 'rgba(141,255,124,0.12)', color: 'var(--nexus-code-text)', border: '0.8px solid rgba(141,255,124,0.3)', borderRadius: 6, padding: '2px 8px', fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.14em' }}>PyTorch</span>
              <span style={{ background: 'rgba(231,255,114,0.12)', color: '#E7FF72', border: '0.8px solid rgba(231,255,114,0.25)', borderRadius: 6, padding: '2px 8px', fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.14em' }}>Autoencoder</span>
            </div>
            <h2 style={{ fontFamily: '"Geist", sans-serif', fontSize: 20, fontWeight: 500, letterSpacing: '-0.03em', color: 'var(--nexus-text-primary)', margin: 0, marginBottom: 8 }}>Anomaly Evaluator</h2>
            <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 13, color: 'var(--nexus-text-muted)', lineHeight: 1.6, margin: 0 }}>
              Submit 8 numeric metrics. Local trained artifacts and validation are required before relying on anomaly output; a default response is not a verified assessment.
            </p>
          </div>

          <div>
            <label style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase' as const, color: 'var(--nexus-text-muted)', display: 'block', marginBottom: 8 }}>API TRANSACTION VECTOR (8 VALUES)</label>
            <input
              type="text"
              value={metricsText}
              onChange={(e) => setMetricsText(e.target.value)}
              placeholder="0.85, 0.92, 0.44, 0.12, 0.76, 0.99, 0.05, 0.81"
              style={{ width: '100%', background: 'var(--nexus-code-bg)', border: '0.8px solid var(--nexus-border)', borderRadius: 10, padding: '12px 14px', fontSize: 12, fontFamily: '"Geist Mono", monospace', color: '#E7FF72', outline: 'none', boxSizing: 'border-box' as const }}
              onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(231,255,114,0.4)'}
              onBlur={(e) => e.currentTarget.style.borderColor = 'var(--nexus-border)'}
            />
            <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 10, color: 'var(--nexus-text-dim)', marginTop: 6, letterSpacing: '0.08em' }}>EXACTLY 8 COMMA-SEPARATED DECIMAL VALUES</p>
          </div>

          {/* Explanation cards */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {[
              { label: 'Experimental', desc: 'No fixed validated threshold', color: 'var(--sev-low)' },
              { label: 'Review required', desc: 'Not incident confirmation', color: 'var(--sev-medium)' },
            ].map((item) => (
              <div key={item.label} style={{ background: 'var(--nexus-input-bg)', border: '0.8px solid var(--nexus-border-soft)', borderRadius: 8, padding: '10px 14px' }}>
                <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.14em', color: item.color, marginBottom: 4 }}>{item.label.toUpperCase()}</p>
                <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 13, color: 'var(--nexus-text-secondary)' }}>{item.desc}</p>
              </div>
            ))}
          </div>

          <button
            onClick={handleAnomalyDetection}
            disabled={anomalyLoading}
            style={{ background: anomalyLoading ? 'rgba(231,255,114,0.3)' : '#E7FF72', color: '#080b12', border: 'none', borderRadius: 10, padding: '12px 20px', fontSize: 11, fontWeight: 700, fontFamily: '"Geist Mono", monospace', letterSpacing: '0.16em', textTransform: 'uppercase' as const, cursor: anomalyLoading ? 'not-allowed' : 'pointer', transition: 'all 150ms ease', marginTop: 'auto' }}
          >
            {anomalyLoading ? 'Evaluating...' : 'Run Anomaly Check →'}
          </button>

          {anomalyResult && <ResultCard data={anomalyResult} type="anomaly" />}
        </div>
      </div>
    </div>
  );
};

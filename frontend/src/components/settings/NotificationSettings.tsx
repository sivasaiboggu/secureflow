import React, { useState } from 'react';
import { FormControlLabel, Switch } from '@mui/material';
import { MessageSquare, Mail, Siren, CheckCircle2 } from 'lucide-react';

const STORAGE_KEY = 'secureflow.notificationPreferences';

/** There is no server endpoint for alerting preferences yet, so choices are
 * stored in this browser's localStorage and the UI says exactly that —
 * saving must never claim a server write that did not happen. */
function loadPreferences(): { slack: boolean; email: boolean; pagerduty: boolean } {
  const defaults = { slack: true, email: true, pagerduty: false };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaults;
    const parsed = JSON.parse(raw);
    return {
      slack: typeof parsed.slack === 'boolean' ? parsed.slack : defaults.slack,
      email: typeof parsed.email === 'boolean' ? parsed.email : defaults.email,
      pagerduty: typeof parsed.pagerduty === 'boolean' ? parsed.pagerduty : defaults.pagerduty,
    };
  } catch {
    return defaults;
  }
}

const CHANNELS = [
  {
    key: 'slack' as const,
    Icon: MessageSquare,
    title: 'Slack',
    desc: 'Route findings to an outage channel webhook.',
  },
  {
    key: 'email' as const,
    Icon: Mail,
    title: 'Email',
    desc: 'Daily compliance summary digest.',
  },
  {
    key: 'pagerduty' as const,
    Icon: Siren,
    title: 'PagerDuty',
    desc: 'Trigger critical incident callouts.',
  },
];

export const NotificationSettings: React.FC = () => {
  const [prefs, setPrefs] = useState(loadPreferences);
  const [message, setMessage] = useState('');

  const handleSave = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
      setMessage('Preferences saved on this browser. There is no server setting for alerting yet, so they do not sync to other devices.');
    } catch {
      setMessage('Could not save preferences in this browser.');
    }
    setTimeout(() => setMessage(''), 6000);
  };

  return (
    <div style={{ padding: '32px', maxWidth: 1400, margin: '0 auto' }}>
      <div style={{ marginBottom: 40, maxWidth: 720 }}>
        <p style={{ fontFamily: '"Geist Mono", monospace', fontSize: 9, letterSpacing: '0.28em', textTransform: 'uppercase' as const, color: 'var(--nexus-text-muted)', marginBottom: 8 }}>ALERTING</p>
        <h1 style={{ fontFamily: '"Geist", sans-serif', fontSize: 32, fontWeight: 500, letterSpacing: '-0.04em', color: 'var(--nexus-text-primary)', margin: 0 }}>Notification Preferences</h1>
        <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 14, color: 'var(--nexus-text-muted)', margin: '8px 0 0', lineHeight: 1.6 }}>
          Route posture scan vulnerabilities automatically to security alerting feeds.
        </p>
      </div>

      <div className="nexus-card" style={{ maxWidth: 720, padding: 28 }}>
        {message && (
          <div role="status" style={{ display: 'flex', gap: 10, alignItems: 'flex-start', background: 'rgba(74,222,128,0.1)', border: '0.8px solid rgba(74,222,128,0.3)', borderRadius: 10, padding: '12px 16px', marginBottom: 20 }}>
            <CheckCircle2 size={16} color="var(--sev-low)" style={{ flexShrink: 0, marginTop: 1 }} />
            <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 13, lineHeight: 1.6, color: 'var(--nexus-text-body)', margin: 0 }}>{message}</p>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {CHANNELS.map(({ key, Icon, title, desc }, i) => (
            <div key={key} className="nexus-row" style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '16px 8px', margin: '0 -8px', borderBottom: i < CHANNELS.length - 1 ? '0.8px solid var(--nexus-border-soft)' : 'none', borderRadius: 8 }}>
              <div style={{ width: 40, height: 40, background: 'var(--nexus-elevated-bg)', border: '0.8px solid var(--nexus-border)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--nexus-accent-text)', flexShrink: 0 }}>
                <Icon size={17} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 15, fontWeight: 500, color: 'var(--nexus-text-primary)', margin: '0 0 3px' }}>{title}</p>
                <p style={{ fontFamily: '"Geist", sans-serif', fontSize: 13, color: 'var(--nexus-text-muted)', margin: 0, lineHeight: 1.5 }}>{desc}</p>
              </div>
              <FormControlLabel
                control={<Switch checked={prefs[key]} onChange={(e) => setPrefs({ ...prefs, [key]: e.target.checked })} />}
                label=""
                sx={{ margin: 0 }}
              />
            </div>
          ))}
        </div>

        <button
          onClick={handleSave}
          style={{ marginTop: 24, background: '#E7FF72', color: '#080b12', border: 'none', borderRadius: 10, padding: '12px 24px', fontSize: 12, fontWeight: 700, fontFamily: '"Geist Mono", monospace', letterSpacing: '0.14em', textTransform: 'uppercase' as const, cursor: 'pointer', transition: 'all 150ms ease' }}
          onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 8px 24px rgba(231,255,114,0.35)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}
        >
          Save Alerting Rules
        </button>
      </div>
    </div>
  );
};

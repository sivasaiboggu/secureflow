import { useState, type FormEvent } from 'react';
import { Mail, MessageSquare, Siren } from 'lucide-react';
import { Notice, PageHeader, SectionHeading } from '../common/Workspace';

const STORAGE_KEY = 'secureflow.notificationPreferences';
const defaults = { slack: true, email: true, pagerduty: false };
type Preferences = typeof defaults;

function loadPreferences(): Preferences {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') as Partial<Preferences>;
    return {
      slack: typeof stored.slack === 'boolean' ? stored.slack : defaults.slack,
      email: typeof stored.email === 'boolean' ? stored.email : defaults.email,
      pagerduty: typeof stored.pagerduty === 'boolean' ? stored.pagerduty : defaults.pagerduty,
    };
  } catch {
    return defaults;
  }
}

const channels = [
  { key: 'slack', icon: MessageSquare, name: 'Slack' },
  { key: 'email', icon: Mail, name: 'Email' },
  { key: 'pagerduty', icon: Siren, name: 'PagerDuty' },
] as const;

export function NotificationSettings() {
  const [prefs, setPrefs] = useState(loadPreferences);
  const [feedback, setFeedback] = useState<'saved' | 'error' | null>(null);

  function save(event: FormEvent) {
    event.preventDefault();
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
      setFeedback('saved');
    } catch {
      setFeedback('error');
    }
  }

  return <div className="page">
    <PageHeader title="Notifications" description="Save your preferred alert channels in this browser." />
    <div className="split">
      <section className="ledger">
        <SectionHeading title="Preferred channels" />
        <form onSubmit={save}>
          {channels.map(({ key, icon: Icon, name }) => <label key={key} className="line-row notification-row">
            <Icon size={20} aria-hidden="true" /><span className="row-title">{name}</span>
            <input type="checkbox" checked={prefs[key]} onChange={event => {
              setPrefs({ ...prefs, [key]: event.target.checked });
              setFeedback(null);
            }} />
          </label>)}
          <div className="section-body stack">
            {feedback === 'saved' && <Notice tone="success">Preferences saved in this browser.</Notice>}
            {feedback === 'error' && <Notice tone="error">This browser could not save your preferences.</Notice>}
            <div className="form-actions"><button type="submit" className="button primary">Save preferences</button></div>
          </div>
        </form>
      </section>
      <aside className="ledger">
        <SectionHeading title="Where these settings apply" />
        <p className="muted section-body">These choices stay on this browser. Alert delivery and device sync require server support.</p>
      </aside>
    </div>
  </div>;
}

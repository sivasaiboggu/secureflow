import React, { useState } from 'react';
import { Container, Paper, Typography, Box, FormControlLabel, Switch, Button, Alert } from '@mui/material';

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
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper sx={{ p: 4, boxShadow: 3 }}>
        <Typography variant="h5" fontWeight="bold" mb={1}>Alerting Channels Preferences</Typography>
        <Typography variant="body2" color="text.secondary" mb={4}>
          Route posture scan vulnerabilities automatically to security alerting feeds.
        </Typography>

        {message && <Alert severity="success" sx={{ mb: 3 }}>{message}</Alert>}

        <Box display="flex" flexDirection="column" gap={2} mb={4}>
          <FormControlLabel
            control={<Switch checked={prefs.slack} onChange={(e) => setPrefs({ ...prefs, slack: e.target.checked })} />}
            label="Slack Integration Webhooks (Enable outage channels alerts)"
          />
          <FormControlLabel
            control={<Switch checked={prefs.email} onChange={(e) => setPrefs({ ...prefs, email: e.target.checked })} />}
            label="Email Alerts (Daily compliance summaries digest)"
          />
          <FormControlLabel
            control={<Switch checked={prefs.pagerduty} onChange={(e) => setPrefs({ ...prefs, pagerduty: e.target.checked })} />}
            label="PagerDuty Escapes (Trigger critical incident callouts)"
          />
        </Box>

        <Button variant="contained" color="primary" onClick={handleSave}>
          Save Alerting Rules
        </Button>
      </Paper>
    </Container>
  );
};

import React, { useState } from 'react';
import { Container, Paper, Typography, Box, FormControlLabel, Switch, Button, Alert } from '@mui/material';

export const NotificationSettings: React.FC = () => {
  const [slack, setSlack] = useState(true);
  const [email, setEmail] = useState(true);
  const [pagerduty, setPagerduty] = useState(false);
  const [message, setMessage] = useState('');

  const handleSave = () => {
    setMessage('Notification preferences updated successfully!');
    setTimeout(() => setMessage(''), 3000);
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
            control={<Switch checked={slack} onChange={(e) => setSlack(e.target.checked)} />}
            label="Slack Integration Webhooks (Enable outage channels alerts)"
          />
          <FormControlLabel
            control={<Switch checked={email} onChange={(e) => setEmail(e.target.checked)} />}
            label="Email Alerts (Daily compliance summaries digest)"
          />
          <FormControlLabel
            control={<Switch checked={pagerduty} onChange={(e) => setPagerduty(e.target.checked)} />}
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

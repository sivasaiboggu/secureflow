import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const userString = localStorage.getItem('user');
  const user = userString ? JSON.parse(userString) : null;

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  return (
    <AppBar position="static" sx={{ bgcolor: '#0f1b29', borderBottom: '1px solid #1e2d3d', boxShadow: 'none' }}>
      <Toolbar>
        <Box sx={{ flexGrow: 1 }} />
        {user && (
          <Typography variant="body2" sx={{ mr: 3, color: 'text.secondary' }}>
            Auditing: {user.email}
          </Typography>
        )}
        <Button variant="outlined" color="secondary" size="small" onClick={handleLogout}>
          Sign Out
        </Button>
      </Toolbar>
    </AppBar>
  );
};

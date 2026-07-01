import React from 'react';
import { Box, List, ListItem, ListItemIcon, ListItemText, Typography } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SearchIcon from '@mui/icons-material/Search';
import BugReportIcon from '@mui/icons-material/BugReport';
import BarChartIcon from '@mui/icons-material/BarChart';

export const Sidebar: React.FC = () => {
  const location = useLocation();
  
  const menuItems = [
    { text: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
    { text: 'Cloud Scans', path: '/scans', icon: <SearchIcon /> },
    { text: 'Vulnerabilities', path: '/vulnerabilities', icon: <BugReportIcon /> },
    { text: 'AI Analytics', path: '/analytics', icon: <BarChartIcon /> }
  ];

  return (
    <Box sx={{ width: 240, bgcolor: '#0f1b29', borderRight: '1px solid #1e2d3d', p: 2 }}>
      <Typography variant="h6" fontWeight="bold" color="primary.main" mb={4}>
        Nexus SecureFlow
      </Typography>
      <List>
        {menuItems.map((item) => (
          <ListItem
            button
            component={Link}
            to={item.path}
            key={item.text}
            selected={location.pathname === item.path}
            sx={{ borderRadius: 1, mb: 1 }}
          >
            <ListItemIcon sx={{ color: location.pathname === item.path ? 'primary.main' : 'inherit' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

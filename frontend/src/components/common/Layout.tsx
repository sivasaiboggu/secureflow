import React from 'react';
import { Box } from '@mui/material';
import { Sidebar } from './Sidebar';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Box display="flex" minHeight="100vh">
      <Sidebar />
      <Box flexGrow={1} display="flex" flexDirection="column" bgcolor="background.default">
        {children}
      </Box>
    </Box>
  );
};

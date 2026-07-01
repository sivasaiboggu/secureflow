import React, { useState } from 'react';
import { Container, Paper, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Box, Button } from '@mui/material';

interface OrgUser {
  email: string;
  name: string;
  role: string;
  status: string;
}

export const UserManagement: React.FC = () => {
  const [users] = useState<OrgUser[]>([
    { email: 'admin@secureflow.io', name: 'Post Posture Auditor', role: 'Administrator', status: 'Active' },
    { email: 'engineer@secureflow.io', name: 'Cloud Operations Dev', role: 'Engineer', status: 'Active' },
    { email: 'readonly@secureflow.io', name: 'Compliance Review Partner', role: 'Viewer', status: 'Active' }
  ]);

  return (
    <Container maxWidth="xl" sx={{ mt: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight="bold">Organization User Directory</Typography>
        <Button variant="contained" disabled>Invite Member</Button>
      </Box>

      <TableContainer component={Paper} sx={{ boxShadow: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Full Name</TableCell>
              <TableCell>Email Address</TableCell>
              <TableCell>Security Role</TableCell>
              <TableCell>Account Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((u) => (
              <TableRow key={u.email}>
                <TableCell>{u.name}</TableCell>
                <TableCell>{u.email}</TableCell>
                <TableCell>
                  <Chip label={u.role} size="small" color={u.role === 'Administrator' ? 'primary' : 'default'} />
                </TableCell>
                <TableCell>
                  <Chip label={u.status} size="small" color="success" variant="outlined" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};

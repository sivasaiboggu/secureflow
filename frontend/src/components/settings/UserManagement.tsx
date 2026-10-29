import React, { useEffect, useState } from 'react';
import { Container, Paper, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Box, Button, CircularProgress, Alert } from '@mui/material';
import { api } from '../../services/api';

interface OrgUser {
  email: string;
  full_name: string | null;
  role: string | null;
  is_active: boolean;
}

export const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<OrgUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await api.get('/users');
        if (!cancelled) setUsers(res.data);
      } catch (err) {
        if (!cancelled) setError('The organization directory could not be loaded.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <Container maxWidth="xl" sx={{ mt: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight="bold">Organization User Directory</Typography>
        <Button variant="contained" disabled title="Invitations are not available yet">Invite Member</Button>
      </Box>

      {error && <Alert severity="warning" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <Box display="flex" justifyContent="center" py={6}><CircularProgress size={36} sx={{ color: '#E7FF72' }} /></Box>
      ) : (
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
              {users.length === 0 && !error ? (
                <TableRow>
                  <TableCell colSpan={4}>No members found for this organization.</TableCell>
                </TableRow>
              ) : (
                users.map((u) => (
                  <TableRow key={u.email}>
                    <TableCell>{u.full_name || 'Not provided'}</TableCell>
                    <TableCell>{u.email}</TableCell>
                    <TableCell>
                      <Chip label={u.role || 'user'} size="small" color={u.role === 'admin' ? 'primary' : 'default'} />
                    </TableCell>
                    <TableCell>
                      <Chip label={u.is_active ? 'Active' : 'Inactive'} size="small" color={u.is_active ? 'success' : 'default'} variant="outlined" />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Container>
  );
};

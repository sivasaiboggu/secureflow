import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { apiMessage, EmptyState, Notice, PageHeader, SectionHeading, Status } from '../common/Workspace';

interface OrgUser { email: string; full_name: string | null; role: string | null; is_active: boolean }

export function UserManagement() {
  const [users, setUsers] = useState<OrgUser[] | null>(null);
  const [error, setError] = useState('');

  async function load(signal?: AbortSignal) {
    setError('');
    try {
      const { data } = await api.get<OrgUser[]>('/users', { signal });
      if (!signal?.aborted) setUsers(data);
    } catch (error) {
      if (!signal?.aborted) setError(apiMessage(error, 'Could not load the organization directory.'));
    }
  }

  useEffect(() => {
    const request = new AbortController();
    void load(request.signal);
    return () => request.abort();
  }, []);

  return <div className="page">
    <PageHeader title="User directory" description="Members, roles and account status in your organization." />
    <section className="ledger">
      <SectionHeading title="Organization members" action={users && <span className="meta">{users.length} shown</span>} />
      {!users && !error && <LoadingSpinner label="Loading members…" />}
      {error && <div className="section-body"><Notice tone="error">{error}
        <div><button type="button" className="text-link" onClick={() => void load()}>Retry</button></div>
      </Notice></div>}
      {users?.length === 0 && <EmptyState title="No organization members found" />}
      {!!users?.length && <div className="table-wrap" tabIndex={0} role="region" aria-label="Organization members table">
        <table className="ledger-table user-table">
          <thead><tr><th scope="col">Name</th><th scope="col">Email</th><th scope="col">Role</th><th scope="col">Status</th></tr></thead>
          <tbody>{users.map(user => <tr key={user.email}>
            <td><span className="row-title">{user.full_name || 'Name unavailable'}</span><small className="table-mobile-detail">{user.email} · {user.role || 'user'}</small></td>
            <td>{user.email}</td>
            <td>{user.role || 'user'}</td>
            <td><Status tone={user.is_active ? 'success' : 'neutral'}>{user.is_active ? 'Active' : 'Inactive'}</Status></td>
          </tr>)}</tbody>
        </table>
      </div>}
    </section>
  </div>;
}

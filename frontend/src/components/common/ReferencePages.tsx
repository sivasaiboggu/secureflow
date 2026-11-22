import { Link } from 'react-router-dom';
import { PageHeader } from './Workspace';

export function ReferencePage({ kind, returnTo }: { kind: 'privacy' | 'usage'; returnTo: string }) {
  const privacy = kind === 'privacy';
  return <div className="page">
    <PageHeader title={privacy ? 'Data and privacy' : 'Usage scope'}
      description={privacy ? 'How this workspace handles data.' : 'What a SecureFlow result covers.'} />
    <div className="ledger reference-copy">
      {privacy ? <>
        <p>A SecureFlow deployment stores user accounts, cloud account records, scan results and saved remediation plans. The browser keeps sign-in tokens until sign-out or session reset. Theme and notification choices stay in the browser.</p>
        <p>Live AWS credentials are encrypted by the server before storage. CloudTrail events and metrics entered in Analytics are sent to that deployment for review.</p>
        <p>Contact your workspace administrator for the privacy policy, retention periods and data requests for this deployment.</p>
      </> : <>
        <p>Use live scans only for cloud accounts your organization has authorized you to assess.</p>
        <p>Demo scans use sample data. Completed live scans cover implemented checks. Review findings and Terraform code before taking action, and follow your organization’s change process.</p>
        <p>Your organization’s terms and policies apply to use of its deployment.</p>
      </>}
      <Link className="text-link" to={returnTo}>Back to SecureFlow</Link>
    </div>
  </div>;
}

export function MissingPage({ returnTo }: { returnTo: string }) {
  return <div className="page">
    <PageHeader title="Page not found" description="Check the address or return to SecureFlow." />
    <Link className="button primary" to={returnTo}>Back to SecureFlow</Link>
  </div>;
}

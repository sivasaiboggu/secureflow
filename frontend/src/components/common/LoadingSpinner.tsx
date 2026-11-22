export function LoadingSpinner({ label = 'Loading this view…' }: { label?: string }) {
  return <div className="loading-state" role="status"><span className="loading-rule" aria-hidden="true" />{label}</div>;
}

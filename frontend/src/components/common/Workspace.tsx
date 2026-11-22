import { useEffect, useId, useRef, type ReactNode } from 'react';
import { AlertCircle, X } from 'lucide-react';
import { Link } from 'react-router-dom';

export function BrandMark() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="brand-mark" fill="none">
      <path d="M4 9V4h5m6 0h5v5m0 6v5h-5m-6 0H4v-5" stroke="currentColor" strokeWidth="1.6" />
      <path d="m8 12 3 3 5-6" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

export function PageHeader({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <header className="page-header">
      <div><h1>{title}</h1><p>{description}</p></div>
      {action && <div className="page-actions">{action}</div>}
    </header>
  );
}

export function SectionHeading({ title, action, id }: { title: string; action?: ReactNode; id?: string }) {
  return <div className="section-heading"><h2 id={id}>{title}</h2>{action}</div>;
}

export function TextLink({ to, children }: { to: string; children: ReactNode }) {
  return <Link className="text-link" to={to}>{children}</Link>;
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return <div className="empty-state"><p><strong>{title}</strong></p>{children}</div>;
}

export function Notice({ children, tone = 'info' }: { children: ReactNode; tone?: 'info' | 'error' | 'success' | 'warning' }) {
  return <div className="notice" data-tone={tone} role={tone === 'error' ? 'alert' : 'status'}><AlertCircle size={17} aria-hidden="true" /><div>{children}</div></div>;
}

export function Status({ children, tone = 'neutral' }: { children: ReactNode; tone?: string }) {
  return <span className="status" data-tone={tone}><span aria-hidden="true" />{children}</span>;
}

export const severityLabels: Readonly<Record<string, string>> = {
  CRITICAL: 'Critical', HIGH: 'High', MEDIUM: 'Medium', LOW: 'Low', INFO: 'Info',
};

export const severityTones: Readonly<Record<string, string>> = {
  CRITICAL: 'error', HIGH: 'high', MEDIUM: 'warning', LOW: 'success',
};

export function Severity({ value }: { value: string }) {
  return <Status tone={severityTones[value]}>{severityLabels[value] ?? value}</Status>;
}

export function Meter({ value, label, tone }: { value: number; label: string; tone?: string }) {
  const percent = Math.min(100, Math.max(0, Number.isFinite(value) ? value : 0));
  return <span className="meter-track" data-tone={tone}>
    <meter className="sr-only" min={0} max={100} value={percent} aria-label={label}>{percent}%</meter>
    <span className="meter-fill" aria-hidden="true" style={{ '--meter-scale': percent / 100 } as React.CSSProperties} />
  </span>;
}

export function Sheet({ title, closeLabel, onClose, drawer = false, children }: {
  title: string; closeLabel: string; onClose: () => void; drawer?: boolean; children: ReactNode;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const id = useId();

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    element.showModal();
    document.body.style.overflow = 'hidden';
    return () => {
      element.close();
      document.body.style.overflow = previousOverflow;
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) previousFocus.focus();
    };
  }, []);

  return (
    <dialog ref={dialog} className={drawer ? 'sheet sheet-drawer' : 'sheet'} aria-labelledby={id}
      onCancel={event => { event.preventDefault(); onClose(); }}
      onClick={event => { if (event.target === event.currentTarget) onClose(); }}>
      <div className="sheet-inner">
        <header className="sheet-header"><h2 id={id}>{title}</h2><button type="button" className="button icon-button" onClick={onClose} aria-label={closeLabel}><X size={18} aria-hidden="true" /></button></header>
        <div className="sheet-body">{children}</div>
      </div>
    </dialog>
  );
}

export function apiMessage(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } } | null)?.response?.data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  return fallback;
}

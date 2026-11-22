import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { X } from 'lucide-react';
import { Notice } from './Workspace';

export type ToastSeverity = 'success' | 'error' | 'info' | 'warning';
const ToastContext = createContext<{ showToast: (message: string, severity?: ToastSeverity) => void }>({ showToast: () => {} });

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<{ message: string; tone: ToastSeverity } | null>(null);
  const showToast = useCallback((message: string, tone: ToastSeverity = 'info') => setToast({ message, tone }), []);

  useEffect(() => {
    if (!toast || toast.tone === 'error') return;
    const timer = window.setTimeout(() => setToast(null), 6000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  return <ToastContext.Provider value={{ showToast }}>
    {children}
    {toast && <div className="toast"><Notice tone={toast.tone}>{toast.message}</Notice>
      <button className="button icon-button" type="button" aria-label="Dismiss message" onClick={() => setToast(null)}><X size={16} aria-hidden="true" /></button>
    </div>}
  </ToastContext.Provider>;
}

export const useToast = () => useContext(ToastContext);

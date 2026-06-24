import * as React from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@/shared/utils';
import { X } from 'lucide-react';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export function Modal({ open, onClose, title, description, children, footer, className }: ModalProps) {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    if (open) {
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  React.useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && open) onClose();
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [open, onClose]);

  if (!mounted) return null;

  return createPortal(
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center p-4',
        open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
      )}
      aria-hidden={!open}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      <div
        className={cn(
          'relative w-full max-w-lg rounded-xl border border-border bg-background-secondary shadow-xl',
          'transform transition-all',
          open ? 'scale-100 translate-y-0' : 'scale-95 translate-y-2',
          className
        )}
      >
        <div className="flex items-start justify-between px-5 py-4 border-b border-border">
          <div>
            <h3 className="text-lg font-semibold text-foreground">{title}</h3>
            {description && <p className="mt-1 text-sm text-foreground-secondary">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-foreground-muted hover:bg-background-tertiary hover:text-foreground"
          >
            <X size={18} />
          </button>
        </div>
        <div className="px-5 py-5 max-h-[70vh] overflow-y-auto">{children}</div>
        {footer && <div className="flex justify-end gap-3 px-5 py-4 border-t border-border">{footer}</div>}
      </div>
    </div>,
    document.body
  );
}

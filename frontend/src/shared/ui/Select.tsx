import { useState, useRef, useEffect } from 'react';
import { cn } from '@/shared/utils';
import { ChevronDown, Search, X } from 'lucide-react';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps {
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  size?: 'sm' | 'md';
  searchable?: boolean;
  'data-testid'?: string;
}

export function Select({
  value,
  options,
  onChange,
  placeholder = '请选择',
  className,
  size = 'md',
  searchable = false,
  'data-testid': testId,
}: SelectProps) {
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const selected = options.find((o) => o.value === value);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  useEffect(() => {
    if (open && searchable) {
      setTimeout(() => searchInputRef.current?.focus(), 10);
    }
    if (!open) {
      setSearchQuery('');
    }
  }, [open, searchable]);

  const filteredOptions = searchable && searchQuery.trim()
    ? options.filter((o) => o.label.toLowerCase().includes(searchQuery.trim().toLowerCase()))
    : options;

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        data-testid={testId}
        className={cn(
          'flex items-center w-full rounded-lg border border-border bg-background',
          size === 'sm' ? 'h-7 px-2 text-xs gap-1.5' : 'h-9 px-3 text-sm gap-2',
          open && 'border-accent'
        )}
      >
        <span className={cn('flex-1 text-left truncate', !selected && 'text-foreground-muted')}>
          {selected ? selected.label : placeholder}
        </span>
        <ChevronDown
          size={size === 'sm' ? 14 : 16}
          className={cn('shrink-0 text-foreground-muted transition-transform', open && 'rotate-180')}
        />
      </button>
      {open && (
        <div className="absolute left-0 top-full z-50 mt-1 rounded-lg border border-border bg-background shadow-lg overflow-hidden min-w-full w-max">
          {searchable && (
            <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
              <Search size={14} className="text-foreground-muted shrink-0" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索..."
                className="flex-1 bg-transparent text-sm text-foreground placeholder:text-foreground-muted outline-none"
                onClick={(e) => e.stopPropagation()}
              />
              {searchQuery && (
                <button
                  onClick={(e) => { e.stopPropagation(); setSearchQuery(''); }}
                  className="shrink-0 text-foreground-muted hover:text-foreground"
                >
                  <X size={14} />
                </button>
              )}
            </div>
          )}
          <div className={cn('overflow-y-auto', searchable && 'max-h-56')}>
            {filteredOptions.length === 0 ? (
              <div className={cn(
                'text-foreground-muted text-center',
                size === 'sm' ? 'px-2 py-2 text-xs' : 'px-3 py-3 text-sm'
              )}>
                无匹配结果
              </div>
            ) : (
              filteredOptions.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => {
                    onChange(opt.value);
                    setOpen(false);
                    setSearchQuery('');
                  }}
                  className={cn(
                    'flex w-full items-center hover:bg-background-tertiary text-left',
                    size === 'sm' ? 'px-2 py-1.5 text-xs' : 'px-3 py-2 text-sm',
                    opt.value === value && 'bg-accent/10 text-accent font-medium'
                  )}
                >
                  {opt.value === value && <span className="mr-2">✓</span>}
                  {opt.label}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

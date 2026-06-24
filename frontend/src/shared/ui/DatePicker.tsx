import { useState, useRef, useEffect, useCallback } from 'react';
import { cn } from '@/shared/utils';
import { ChevronLeft, ChevronRight, CalendarDays } from 'lucide-react';

const WEEKDAY_CN = ['日', '一', '二', '三', '四', '五', '六'];
const MONTH_CN = [
  '一月', '二月', '三月', '四月', '五月', '六月',
  '七月', '八月', '九月', '十月', '十一月', '十二月',
];

function fmtChineseDate(iso: string): string {
  const [y, m, d] = iso.split('-');
  return `${y}年${Number(m)}月${Number(d)}日`;
}

function toLocalDateStr(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function getMonthDays(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year: number, month: number): number {
  return new Date(year, month, 1).getDay();
}

function parseValue(value: string): { year: number; month: number } {
  if (!value) {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() };
  }
  const parts = value.split('-').map(Number);
  return { year: parts[0], month: parts[1] - 1 };
}

export interface DatePickerProps {
  value: string;
  onChange: (date: string) => void;
  label?: string;
  placeholder?: string;
  minDate?: string;
  maxDate?: string;
  align?: 'left' | 'right';
  mode?: 'date' | 'month';
  disabled?: boolean;
  className?: string;
}

export function DatePicker({
  value,
  onChange,
  label,
  placeholder = '请选择',
  minDate,
  maxDate,
  align = 'left',
  mode = 'date',
  disabled = false,
  className,
}: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const [popupStyle, setPopupStyle] = useState<React.CSSProperties>({});
  const containerRef = useRef<HTMLDivElement>(null);
  const btnRef = useRef<HTMLButtonElement>(null);

  const { year: initialYear, month: initialMonth } = parseValue(value);
  const [viewYear, setViewYear] = useState(initialYear);
  const [viewMonth, setViewMonth] = useState(initialMonth);

  useEffect(() => {
    const { year, month } = parseValue(value);
    setViewYear(year);
    setViewMonth(month);
  }, [value]);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  const daysInMonth = getMonthDays(viewYear, viewMonth);
  const firstDay = getFirstDayOfMonth(viewYear, viewMonth);
  const today = toLocalDateStr(new Date());

  const handlePrevMonth = useCallback(() => {
    if (viewMonth === 0) {
      setViewYear((y) => y - 1);
      setViewMonth(11);
    } else {
      setViewMonth((m) => m - 1);
    }
  }, [viewMonth]);

  const handleNextMonth = useCallback(() => {
    if (viewMonth === 11) {
      setViewYear((y) => y + 1);
      setViewMonth(0);
    } else {
      setViewMonth((m) => m + 1);
    }
  }, [viewMonth]);

  const handleOpen = useCallback(() => {
    if (disabled) return;
    if (btnRef.current) {
      const rect = btnRef.current.getBoundingClientRect();
      const popupWidth = 288;
      const spaceRight = window.innerWidth - rect.right;
      const left = spaceRight < popupWidth ? rect.right - popupWidth : rect.left;
      const spaceBelow = window.innerHeight - rect.bottom;
      const popupHeight = mode === 'month' ? 260 : 360;
      const top = spaceBelow >= popupHeight ? rect.bottom + 4 : rect.top - popupHeight - 4;
      setPopupStyle({ position: 'fixed', top: Math.max(8, top), left: Math.max(8, left) });
    }
    setOpen(true);
  }, [disabled, mode]);

  const handleSelectDay = (day: number) => {
    const y = String(viewYear).padStart(4, '0');
    const m = String(viewMonth + 1).padStart(2, '0');
    const d = String(day).padStart(2, '0');
    const iso = `${y}-${m}-${d}`;
    if (minDate && iso < minDate) return;
    if (maxDate && iso > maxDate) return;
    onChange(iso);
    setOpen(false);
  };

  const handleSelectMonth = (monthIdx: number) => {
    const y = String(viewYear).padStart(4, '0');
    const m = String(monthIdx + 1).padStart(2, '0');
    const iso = `${y}-${m}`;
    if (minDate && iso < minDate.slice(0, 7)) return;
    if (maxDate && iso > maxDate.slice(0, 7)) return;
    onChange(iso);
    setOpen(false);
  };

  const isDisabled = (day: number) => {
    const y = String(viewYear).padStart(4, '0');
    const m = String(viewMonth + 1).padStart(2, '0');
    const d = String(day).padStart(2, '0');
    const iso = `${y}-${m}-${d}`;
    if (minDate && iso < minDate) return true;
    if (maxDate && iso > maxDate) return true;
    return false;
  };

  const cells: (number | null)[] = Array(firstDay).fill(null);
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push(d);
  }

  const displayText = value
    ? mode === 'month'
      ? `${value.split('-')[0]}年${String(value.split('-')[1]).padStart(2, '0')}月`
      : fmtChineseDate(value)
    : placeholder;

  return (
    <div ref={containerRef} className={cn('space-y-1.5', className)}>
      {label && <label className="text-sm font-medium text-foreground">{label}</label>}
      <button
        ref={btnRef}
        type="button"
        onClick={open ? () => setOpen(false) : handleOpen}
        disabled={disabled}
        className={cn(
          'flex h-10 w-full items-center gap-2 rounded-lg border px-3 text-sm',
          'border-border bg-background-tertiary text-foreground',
          disabled ? 'opacity-50 cursor-not-allowed' : 'transition-colors hover:border-foreground'
        )}
      >
        <CalendarDays size={16} className={cn('shrink-0', value ? 'text-foreground' : 'text-foreground-muted')} />
        <span className={cn('flex-1 text-left tabular-nums', !value && 'text-foreground-muted')}>
          {displayText}
        </span>
      </button>

      {open && (
        <div
          style={popupStyle}
          className="z-50 w-72 rounded-xl border border-border bg-background-secondary p-4 shadow-xl"
        >
          <div className="mb-3 flex items-center justify-between">
            <button
              onClick={handlePrevMonth}
              className="flex h-7 w-7 items-center justify-center rounded-md text-foreground-secondary transition-colors hover:bg-background-tertiary hover:text-foreground"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-sm font-semibold text-foreground">
              {viewYear}年{MONTH_CN[viewMonth]}
            </span>
            <button
              onClick={handleNextMonth}
              className="flex h-7 w-7 items-center justify-center rounded-md text-foreground-secondary transition-colors hover:bg-background-tertiary hover:text-foreground"
            >
              <ChevronRight size={16} />
            </button>
          </div>

          {mode === 'month' ? (
            <div className="grid grid-cols-4 gap-2">
              {MONTH_CN.map((_, idx) => {
                const iso = `${String(viewYear).padStart(4, '0')}-${String(idx + 1).padStart(2, '0')}`;
                const isSelected = iso === value;
                return (
                  <button
                    key={iso}
                    onClick={() => handleSelectMonth(idx)}
                    className={cn(
                      'flex h-10 items-center justify-center rounded-md text-sm font-medium transition-colors',
                      isSelected
                        ? 'bg-accent text-white'
                        : 'text-foreground hover:bg-background-tertiary'
                    )}
                  >
                    {idx + 1}月
                  </button>
                );
              })}
            </div>
          ) : (
            <>
              <div className="mb-2 grid grid-cols-7 gap-0.5">
                {WEEKDAY_CN.map((w) => (
                  <div key={w} className="flex h-8 items-center justify-center text-xs font-medium text-foreground-secondary">
                    {w}
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-0.5">
                {cells.map((day, i) => {
                  if (day === null) return <div key={`empty-${i}`} />;
                  const iso = `${String(viewYear).padStart(4, '0')}-${String(viewMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                  const isSelected = iso === value;
                  const isToday = iso === today;
                  const disabledDay = isDisabled(day);
                  return (
                    <button
                      key={iso}
                      onClick={() => handleSelectDay(day)}
                      disabled={disabledDay}
                      className={cn(
                        'flex h-9 items-center justify-center rounded-md text-sm font-semibold transition-colors',
                        isSelected
                          ? 'bg-accent text-white'
                          : isToday
                            ? 'text-accent'
                            : 'text-foreground hover:bg-background-tertiary',
                        disabledDay && 'opacity-30 cursor-not-allowed'
                      )}
                    >
                      {day}
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

import { useState, useRef, useEffect, useMemo } from 'react';
import { cn } from '@/shared/utils';
import {
  DatePicker as HeroUIDatePicker,
  DateField,
  Calendar,
} from '@heroui/react';
import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react';
import { parseDate } from '@internationalized/date';
import type { DateValue } from '@internationalized/date';

const MONTH_CN = [
  '一月', '二月', '三月', '四月', '五月', '六月',
  '七月', '八月', '九月', '十月', '十一月', '十二月',
];

export interface DatePickerProps {
  value: string;
  onChange: (date: string) => void;
  label?: string;
  placeholder?: string;
  minDate?: string;
  maxDate?: string;
  mode?: 'date' | 'month';
  disabled?: boolean;
  className?: string;
}

function toCalendarDate(value: string): DateValue | null {
  if (!value) return null;
  try {
    return parseDate(value);
  } catch {
    return null;
  }
}

function dateValueToString(value: DateValue | null): string {
  if (!value) return '';
  return value.toString();
}

function MonthPicker({
  value,
  onChange,
  label,
  placeholder,
  disabled,
  className,
}: Omit<DatePickerProps, 'mode' | 'minDate' | 'maxDate'>) {
  const [open, setOpen] = useState(false);
  const [viewYear, setViewYear] = useState(() => {
    const y = value ? Number(value.split('-')[0]) : new Date().getFullYear();
    return Number.isNaN(y) ? new Date().getFullYear() : y;
  });
  const containerRef = useRef<HTMLDivElement>(null);
  const btnRef = useRef<HTMLButtonElement>(null);

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

  const displayText = value
    ? `${value.split('-')[0]}年${String(value.split('-')[1]).padStart(2, '0')}月`
    : placeholder;

  const handleSelect = (monthIdx: number) => {
    const iso = `${viewYear}-${String(monthIdx + 1).padStart(2, '0')}`;
    onChange(iso);
    setOpen(false);
  };

  return (
    <div ref={containerRef} className={cn('relative space-y-1.5', className)}>
      {label && <label className="text-sm font-medium text-foreground">{label}</label>}
      <button
        ref={btnRef}
        type="button"
        disabled={disabled}
        onClick={() => !disabled && setOpen((v) => !v)}
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
        <div className="absolute z-50 mt-1 w-64 rounded-xl border border-border bg-background-secondary p-3 shadow-xl">
          <div className="mb-2 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setViewYear((y) => y - 1)}
              className="flex h-7 w-7 items-center justify-center rounded-md text-foreground-secondary transition-colors hover:bg-background-tertiary hover:text-foreground"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-sm font-semibold text-foreground">{viewYear}年</span>
            <button
              type="button"
              onClick={() => setViewYear((y) => y + 1)}
              className="flex h-7 w-7 items-center justify-center rounded-md text-foreground-secondary transition-colors hover:bg-background-tertiary hover:text-foreground"
            >
              <ChevronRight size={16} />
            </button>
          </div>
          <div className="grid grid-cols-4 gap-1">
            {MONTH_CN.map((name, idx) => {
              const iso = `${viewYear}-${String(idx + 1).padStart(2, '0')}`;
              const isSelected = iso === value;
              return (
                <button
                  key={name}
                  type="button"
                  onClick={() => handleSelect(idx)}
                  className={cn(
                    'flex h-9 items-center justify-center rounded-md text-xs font-medium transition-colors',
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
        </div>
      )}
    </div>
  );
}

export function DatePicker({
  value,
  onChange,
  label,
  placeholder = '请选择',
  minDate,
  maxDate,
  mode = 'date',
  disabled = false,
  className,
}: DatePickerProps) {
  if (mode === 'month') {
    return (
      <MonthPicker
        value={value}
        onChange={onChange}
        label={label}
        placeholder={placeholder}
        disabled={disabled}
        className={className}
      />
    );
  }

  const dateValue = useMemo(() => toCalendarDate(value), [value]);
  const minValue = useMemo(() => (minDate ? parseDate(minDate) : undefined), [minDate]);
  const maxValue = useMemo(() => (maxDate ? parseDate(maxDate) : undefined), [maxDate]);

  const handleChange = (val: DateValue | null) => {
    onChange(dateValueToString(val));
  };

  return (
    <div className={cn('space-y-1.5', className)}>
      {label && <label className="text-sm font-medium text-foreground">{label}</label>}
      <HeroUIDatePicker
        value={dateValue}
        onChange={handleChange}
        minValue={minValue}
        maxValue={maxValue}
        isDisabled={disabled}
        className="w-full"
      >
        <DateField.Group
          className={cn(
            'flex h-10 w-full items-center gap-2 rounded-lg border px-3 text-sm',
            'border-border bg-background-tertiary text-foreground',
            disabled ? 'opacity-50 cursor-not-allowed' : 'transition-colors hover:border-foreground'
          )}
        >
          <CalendarDays size={16} className={cn('shrink-0', value ? 'text-foreground' : 'text-foreground-muted')} />
          <DateField.Input className="flex-1 bg-transparent outline-none">
            {(segment) => <DateField.Segment segment={segment} className="text-foreground data-[placeholder]:text-foreground-muted" />}
          </DateField.Input>
          <DateField.Suffix>
            <HeroUIDatePicker.Trigger className="text-foreground-muted hover:text-foreground">
              <HeroUIDatePicker.TriggerIndicator />
            </HeroUIDatePicker.Trigger>
          </DateField.Suffix>
        </DateField.Group>
        <HeroUIDatePicker.Popover className="rounded-xl border border-border bg-background-secondary p-2 shadow-xl">
          <Calendar aria-label={label || '选择日期'}>
            <Calendar.Header className="flex items-center justify-between px-2 py-1">
              <Calendar.YearPickerTrigger>
                <Calendar.YearPickerTriggerHeading />
                <Calendar.YearPickerTriggerIndicator />
              </Calendar.YearPickerTrigger>
              <div className="flex gap-1">
                <Calendar.NavButton slot="previous" />
                <Calendar.NavButton slot="next" />
              </div>
            </Calendar.Header>
            <Calendar.Grid>
              <Calendar.GridHeader>
                {(day) => <Calendar.HeaderCell>{day}</Calendar.HeaderCell>}
              </Calendar.GridHeader>
              <Calendar.GridBody>
                {(date) => <Calendar.Cell date={date} />}
              </Calendar.GridBody>
            </Calendar.Grid>
          </Calendar>
        </HeroUIDatePicker.Popover>
      </HeroUIDatePicker>
    </div>
  );
}

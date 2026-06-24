import { type ClassValue, clsx } from 'clsx';
import { extendTailwindMerge } from 'tailwind-merge';

/**
 * Custom twMerge that knows about our design-token overrides.
 *
 * Our borderRadius scale differs from Tailwind defaults:
 *   lg=0.25rem (4px)  vs default 0.5rem
 *   xl=0.5rem  (8px)  vs default 0.75rem
 *   2xl=0.75rem (12px) vs default 1rem
 */
const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      radius: ['lg', 'xl', '2xl'],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

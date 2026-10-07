'use client';

import { cn } from '../../lib/utils/cn';
import { useT } from '@/lib/i18n/context';

type LogoProps = {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
};

const sizes = {
  sm: { box: 'h-8 w-8', text: 'text-sm' },
  md: { box: 'h-10 w-10', text: 'text-base' },
  lg: { box: 'h-14 w-14', text: 'text-xl' },
};

export function Logo({ className, size = 'md', showText = true }: LogoProps) {
  const { t } = useT();
  const s = sizes[size];
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div
        className={cn(
          'relative flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-700 shadow-lg shadow-emerald-900/40',
          s.box
        )}
      >
        <svg viewBox="0 0 40 40" className="h-[60%] w-[60%]" aria-hidden>
          <circle
            cx="20"
            cy="20"
            r="14"
            fill="none"
            stroke="white"
            strokeWidth="2.5"
            strokeDasharray="8 4"
            opacity="0.95"
          />
          <path
            d="M14 22c4-8 12-10 16-6-2 6-8 10-14 8z"
            fill="white"
            opacity="0.95"
          />
          <circle cx="20" cy="20" r="3" fill="white" opacity="0.9" />
        </svg>
      </div>
      {showText && (
        <div className="leading-tight">
          <div className={cn('font-bold tracking-tight text-slate-900', s.text)}>
            CMEP
          </div>
          <div className="text-[10px] font-medium uppercase tracking-wider text-emerald-700">
            {t('logo.brand')}
          </div>
        </div>
      )}
    </div>
  );
}

/** alias pre LoginPage a staršie importy */
export const BrandLogo = Logo;
export default Logo;

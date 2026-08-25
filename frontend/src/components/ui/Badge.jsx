/**
 * Premium Status badge with glassmorphism, glowing indicator dots, and crisp typography.
 *
 * @param {'info'|'success'|'warning'|'danger'|'neutral'|'primary'|'accent'} variant
 * @param {'xs'|'sm'|'md'|'lg'} size
 * @param {boolean} dot — shows an indicator status dot
 * @param {boolean} pulse — animates the status dot with a soft ping
 */
const Badge = ({
  children,
  variant = 'neutral',
  size = 'md',
  dot = false,
  pulse = false,
  className = '',
  ...props
}) => {
  const variantStyles = {
    info: 'bg-primary-50/80 text-primary-700 border border-primary-200/90 shadow-sm',
    primary: 'bg-gradient-to-r from-primary-600 to-indigo-600 text-white border border-indigo-400/40 shadow-sm',
    accent: 'bg-accent-50/90 text-accent-800 border border-accent-200/90 shadow-sm',
    success: 'bg-emerald-50/90 text-emerald-800 border border-emerald-200/90 shadow-sm',
    warning: 'bg-amber-50/90 text-amber-800 border border-amber-200/90 shadow-sm',
    danger: 'bg-rose-50/90 text-rose-800 border border-rose-200/90 shadow-sm',
    neutral: 'bg-slate-100/90 text-slate-700 border border-slate-200/80 shadow-sm',
  };

  const dotColors = {
    info: 'bg-primary-500 shadow-glow-primary',
    primary: 'bg-white',
    accent: 'bg-accent-500 shadow-glow-accent',
    success: 'bg-emerald-500 shadow-glow-success',
    warning: 'bg-amber-500',
    danger: 'bg-rose-500 shadow-glow-danger',
    neutral: 'bg-slate-400',
  };

  const sizeStyles = {
    xs: 'px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider',
    sm: 'px-2.5 py-0.5 text-xs font-semibold',
    md: 'px-3 py-1 text-xs font-semibold',
    lg: 'px-3.5 py-1 text-sm font-semibold',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-full
        transition-all duration-200 backdrop-blur-md
        ${variantStyles[variant] || variantStyles.neutral}
        ${sizeStyles[size] || sizeStyles.md}
        ${className}
      `}
      {...props}
    >
      {dot && (
        <span className="relative flex h-2 w-2 shrink-0">
          {pulse && (
            <span
              className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${dotColors[variant] || 'bg-slate-400'}`}
            />
          )}
          <span
            className={`relative inline-flex rounded-full h-2 w-2 ${dotColors[variant] || 'bg-slate-400'}`}
          />
        </span>
      )}
      <span>{children}</span>
    </span>
  );
};

export default Badge;

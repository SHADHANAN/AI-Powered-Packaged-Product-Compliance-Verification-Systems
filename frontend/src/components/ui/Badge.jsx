/**
 * Command Center Status Badge with high-contrast colors and dot indicators.
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
    info: 'bg-indigo-50 text-indigo-700 border border-indigo-200',
    primary: 'bg-primary-600 text-white border border-primary-700 font-bold',
    accent: 'bg-cyan-50 text-cyan-800 border border-cyan-200',
    success: 'bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold',
    warning: 'bg-amber-50 text-amber-800 border border-amber-200 font-semibold',
    danger: 'bg-rose-50 text-rose-800 border border-rose-200 font-semibold',
    neutral: 'bg-slate-100 text-slate-700 border border-slate-200',
  };

  const dotColors = {
    info: 'bg-indigo-500',
    primary: 'bg-white',
    accent: 'bg-cyan-500',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-rose-500',
    neutral: 'bg-slate-400',
  };

  const sizeStyles = {
    xs: 'px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider',
    sm: 'px-2.5 py-0.5 text-xs font-semibold',
    md: 'px-3 py-1 text-xs font-semibold',
    lg: 'px-3.5 py-1.5 text-sm font-bold',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-lg
        transition-colors duration-150
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

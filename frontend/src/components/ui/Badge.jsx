/**
 * Status badge with semantic color variants.
 *
 * @param {'info'|'success'|'warning'|'danger'|'neutral'|'primary'} variant
 * @param {'sm'|'md'|'lg'} size
 * @param {boolean} dot — shows a status indicator dot
 * @param {boolean} pulse — animates the dot
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
    info: 'bg-primary-50 text-primary-700 ring-primary-200',
    success: 'bg-accent-50 text-accent-700 ring-accent-200',
    warning: 'bg-warning-50 text-warning-700 ring-warning-200',
    danger: 'bg-danger-50 text-danger-700 ring-danger-200',
    neutral: 'bg-surface-100 text-surface-600 ring-surface-200',
    primary: 'bg-primary-600 text-white ring-primary-400',
  };

  const dotColors = {
    info: 'bg-primary-500',
    success: 'bg-accent-500',
    warning: 'bg-warning-500',
    danger: 'bg-danger-500',
    neutral: 'bg-surface-400',
    primary: 'bg-white',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1 text-sm',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 font-medium rounded-full
        ring-1 ring-inset transition-colors duration-200
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
      {...props}
    >
      {dot && (
        <span className="relative flex h-2 w-2">
          {pulse && (
            <span
              className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${dotColors[variant]}`}
            />
          )}
          <span
            className={`relative inline-flex rounded-full h-2 w-2 ${dotColors[variant]}`}
          />
        </span>
      )}
      {children}
    </span>
  );
};

export default Badge;

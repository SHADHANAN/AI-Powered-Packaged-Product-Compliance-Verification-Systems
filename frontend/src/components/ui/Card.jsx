/**
 * Command Center Card component with crisp borders and subtle elevation.
 *
 * @param {'default'|'hero'|'elevated'|'outlined'|'glass'} variant
 * @param {boolean} hoverable — adds subtle lift on hover
 * @param {boolean} noPadding
 */
const Card = ({
  children,
  variant = 'default',
  hoverable = false,
  noPadding = false,
  className = '',
  header,
  footer,
  ...props
}) => {
  const variantStyles = {
    default: 'cmd-card',
    hero: 'cmd-hero text-white',
    elevated: 'bg-white border border-slate-200 rounded-2xl shadow-card',
    outlined: 'bg-white/60 border border-slate-200/90 rounded-2xl',
    glass: 'bg-white/90 backdrop-blur-md border border-slate-200/80 rounded-2xl shadow-card',
  };

  return (
    <div
      className={`
        transition-all duration-200 ease-out
        ${variantStyles[variant] || variantStyles.default}
        ${hoverable ? 'cmd-card-hover cursor-pointer' : ''}
        ${className}
      `}
      {...props}
    >
      {header && (
        <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
          {typeof header === 'string' ? (
            <h3 className="text-xs font-bold uppercase tracking-wider text-command-900">{header}</h3>
          ) : (
            header
          )}
        </div>
      )}

      <div className={noPadding ? '' : 'p-5 sm:p-6'}>{children}</div>

      {footer && (
        <div className="px-5 py-3 border-t border-slate-100 bg-slate-50/50 rounded-b-2xl">
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;

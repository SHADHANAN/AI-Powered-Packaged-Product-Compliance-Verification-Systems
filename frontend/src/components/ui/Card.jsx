/**
 * Premium Reusable Card component supporting Glassmorphism and Bento-Grid tiles.
 *
 * @param {'default'|'glass'|'bento'|'elevated'|'outlined'|'dark'} variant
 * @param {boolean} hoverable — adds smooth lift effect and subtle border glow on hover
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
    default: 'glass-panel',
    glass: 'glass-panel',
    bento: 'glass-bento',
    elevated: 'bg-white/90 backdrop-blur-md shadow-glass-md border border-slate-200/90',
    outlined: 'bg-white/50 backdrop-blur-sm border border-slate-200/80',
    dark: 'bg-gradient-to-br from-navy-950 via-navy-900 to-slate-900 text-white border border-white/10 shadow-glass-lg',
  };

  return (
    <div
      className={`
        rounded-2xl transition-all duration-300 ease-out
        ${variantStyles[variant] || variantStyles.default}
        ${hoverable ? 'glass-panel-hover cursor-pointer' : ''}
        ${className}
      `}
      {...props}
    >
      {header && (
        <div className="px-5 py-4 border-b border-slate-100/80">
          {typeof header === 'string' ? (
            <h3 className="text-base font-bold text-navy-900 tracking-tight">{header}</h3>
          ) : (
            header
          )}
        </div>
      )}

      <div className={noPadding ? '' : 'p-5 sm:p-6'}>{children}</div>

      {footer && (
        <div className="px-5 py-3.5 border-t border-slate-100/80 bg-slate-50/50 rounded-b-2xl">
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;

/**
 * Reusable Card component with glass-morphism styling.
 *
 * @param {'default'|'glass'|'outlined'|'elevated'} variant
 * @param {boolean} hoverable — adds a lift effect on hover
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
    default: 'bg-white border border-surface-200 shadow-sm',
    glass: 'glass-card',
    outlined: 'bg-transparent border-2 border-surface-200',
    elevated: 'bg-white shadow-glass border border-surface-100',
  };

  return (
    <div
      className={`
        rounded-2xl transition-all duration-300 ease-out animate-fade-in
        ${variantStyles[variant]}
        ${hoverable ? 'hover:shadow-glass-lg hover:-translate-y-0.5 cursor-pointer' : ''}
        ${className}
      `}
      {...props}
    >
      {header && (
        <div className="px-5 py-4 border-b border-surface-100">
          {typeof header === 'string' ? (
            <h3 className="text-lg font-semibold text-surface-800">{header}</h3>
          ) : (
            header
          )}
        </div>
      )}

      <div className={noPadding ? '' : 'p-5'}>{children}</div>

      {footer && (
        <div className="px-5 py-3 border-t border-surface-100 bg-surface-50/50 rounded-b-2xl">
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;

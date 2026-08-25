import { forwardRef } from 'react';

const variantStyles = {
  primary:
    'bg-primary-600 text-white hover:bg-primary-500 shadow-sm hover:shadow-glow-primary focus-visible:ring-primary-500 border border-primary-500',
  secondary:
    'bg-white text-command-900 hover:bg-slate-50 focus-visible:ring-primary-500 border border-slate-200 shadow-card hover:border-slate-300',
  accent:
    'bg-cyan-600 text-white hover:bg-cyan-500 shadow-sm hover:shadow-glow-cyan focus-visible:ring-cyan-400 border border-cyan-500',
  success:
    'bg-success-600 text-white hover:bg-success-500 shadow-sm hover:shadow-glow-emerald focus-visible:ring-success-500 border border-success-500',
  danger:
    'bg-danger-600 text-white hover:bg-danger-500 shadow-sm hover:shadow-glow-danger focus-visible:ring-danger-500 border border-danger-500',
  ghost:
    'bg-transparent text-slate-600 hover:bg-slate-100 hover:text-command-900 focus-visible:ring-primary-400',
  outline:
    'bg-transparent text-primary-600 border border-primary-300 hover:bg-primary-50 hover:border-primary-400 focus-visible:ring-primary-500',
  hero:
    'bg-gradient-to-r from-primary-600 to-indigo-500 text-white hover:from-primary-500 hover:to-indigo-400 shadow-glow-primary border border-white/20',
};

const sizeStyles = {
  xs: 'px-2.5 py-1 text-xs rounded-md gap-1 font-semibold',
  sm: 'px-3 py-1.5 text-xs rounded-lg gap-1.5 font-semibold',
  md: 'px-4 py-2 text-xs sm:text-sm rounded-lg gap-2 font-semibold',
  lg: 'px-5 py-2.5 text-sm sm:text-base rounded-xl gap-2 font-bold',
  xl: 'px-6 py-3 text-base rounded-xl gap-2.5 font-bold',
};

/**
 * Command Center Button component.
 */
const Button = forwardRef(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      loading = false,
      disabled = false,
      fullWidth = false,
      leftIcon,
      rightIcon,
      className = '',
      type = 'button',
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        className={`
          inline-flex items-center justify-center
          transition-all duration-150 ease-out
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
          disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
          active:scale-[0.98]
          ${variantStyles[variant] || variantStyles.primary}
          ${sizeStyles[size] || sizeStyles.md}
          ${fullWidth ? 'w-full' : ''}
          ${className}
        `}
        {...props}
      >
        {loading ? (
          <svg
            className="animate-spin h-4 w-4 text-current"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : (
          leftIcon
        )}
        <span>{children}</span>
        {!loading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;

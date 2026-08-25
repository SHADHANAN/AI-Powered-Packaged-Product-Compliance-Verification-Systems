import { forwardRef } from 'react';

const variantStyles = {
  primary:
    'bg-gradient-to-r from-primary-600 to-indigo-600 text-white hover:from-primary-500 hover:to-indigo-500 shadow-sm hover:shadow-glow-primary focus-visible:ring-primary-500 border border-indigo-400/30',
  secondary:
    'bg-white/80 text-navy-800 hover:bg-white hover:text-navy-950 focus-visible:ring-primary-400 border border-slate-200/80 shadow-sm hover:shadow-md backdrop-blur-md',
  accent:
    'bg-gradient-to-r from-accent-600 to-cyan-500 text-white hover:from-accent-500 hover:to-cyan-400 shadow-sm hover:shadow-glow-accent focus-visible:ring-accent-400 border border-cyan-400/30',
  success:
    'bg-gradient-to-r from-success-600 to-emerald-600 text-white hover:from-success-500 hover:to-emerald-500 shadow-sm hover:shadow-glow-success focus-visible:ring-success-500 border border-emerald-400/30',
  danger:
    'bg-gradient-to-r from-danger-600 to-rose-600 text-white hover:from-danger-500 hover:to-rose-500 shadow-sm hover:shadow-glow-danger focus-visible:ring-danger-500 border border-rose-400/30',
  ghost:
    'bg-transparent text-navy-600 hover:bg-slate-100/80 hover:text-navy-900 focus-visible:ring-primary-400',
  outline:
    'bg-transparent text-primary-600 border border-primary-300 hover:bg-primary-50/60 hover:border-primary-400 focus-visible:ring-primary-500',
};

const sizeStyles = {
  xs: 'px-2.5 py-1 text-xs rounded-lg gap-1 font-medium',
  sm: 'px-3.5 py-1.5 text-xs sm:text-sm rounded-xl gap-1.5 font-semibold',
  md: 'px-4 py-2 text-sm rounded-xl gap-2 font-semibold',
  lg: 'px-5 py-2.5 text-base rounded-xl gap-2.5 font-semibold',
  xl: 'px-6 py-3 text-lg rounded-2xl gap-3 font-bold',
};

/**
 * Premium Reusable Button component with glassmorphism, micro-interactions, and gradient glow.
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
          transition-all duration-200 ease-out
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

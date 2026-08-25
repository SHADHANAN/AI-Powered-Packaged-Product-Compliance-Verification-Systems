import { forwardRef, useState } from 'react';

/**
 * Premium Glass Input component with floating label feel, validation states,
 * and icon support.
 */
const Input = forwardRef(
  (
    {
      label,
      type = 'text',
      size = 'md',
      error,
      helperText,
      leftIcon,
      rightIcon,
      className = '',
      id,
      disabled = false,
      required = false,
      ...props
    },
    ref
  ) => {
    const [focused, setFocused] = useState(false);

    const inputId = id || `input-${label?.toLowerCase().replace(/\s+/g, '-') || 'field'}`;

    const sizeStyles = {
      sm: 'py-2 text-xs sm:text-sm',
      md: 'py-2.5 text-sm',
      lg: 'py-3 text-base',
    };

    return (
      <div className={`w-full ${className}`}>
        {label && (
          <label
            htmlFor={inputId}
            className={`
              block text-xs font-bold mb-1.5 transition-colors duration-200 uppercase tracking-wider
              ${focused ? 'text-primary-600' : 'text-navy-700'}
              ${error ? 'text-danger-600' : ''}
            `}
          >
            {label}
            {required && <span className="text-danger-500 ml-1">*</span>}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-navy-400">
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            type={type}
            disabled={disabled}
            required={required}
            onFocus={(e) => {
              setFocused(true);
              props.onFocus?.(e);
            }}
            onBlur={(e) => {
              setFocused(false);
              props.onBlur?.(e);
            }}
            className={`
              block w-full rounded-xl bg-white/80 backdrop-blur-md
              placeholder:text-slate-400 text-navy-900 font-medium
              transition-all duration-200
              focus:outline-none focus:bg-white
              disabled:bg-slate-100/60 disabled:text-slate-400 disabled:cursor-not-allowed
              ${sizeStyles[size] || sizeStyles.md}
              ${leftIcon ? 'pl-11' : 'px-4'}
              ${rightIcon ? 'pr-11' : 'px-4'}
              ${
                error
                  ? 'border border-danger-400 focus:border-danger-500 focus:ring-2 focus:ring-danger-200'
                  : 'border border-slate-200/90 focus:border-primary-500 focus:ring-2 focus:ring-primary-100 shadow-sm'
              }
            `}
            {...props}
          />

          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-navy-400">
              {rightIcon}
            </div>
          )}
        </div>

        {(error || helperText) && (
          <p
            className={`mt-1.5 text-xs ${
              error ? 'text-danger-600 font-medium' : 'text-slate-500'
            }`}
          >
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;

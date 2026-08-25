import { forwardRef, useState } from 'react';

/**
 * Reusable Input component with floating-label feel, validation states,
 * and icon support.
 *
 * @param {'text'|'email'|'password'|'number'|'search'|'tel'|'url'} type
 * @param {'sm'|'md'|'lg'} size
 * @param {string} error — error message; renders red border + message
 * @param {React.ReactNode} leftIcon
 * @param {React.ReactNode} rightIcon
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
      sm: 'py-1.5 text-sm',
      md: 'py-2 text-sm',
      lg: 'py-2.5 text-base',
    };

    return (
      <div className={`w-full ${className}`}>
        {label && (
          <label
            htmlFor={inputId}
            className={`
              block text-sm font-medium mb-1.5 transition-colors duration-200
              ${focused ? 'text-primary-600' : 'text-surface-700'}
              ${error ? 'text-danger-600' : ''}
            `}
          >
            {label}
            {required && <span className="text-danger-500 ml-0.5">*</span>}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-surface-400">
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
              block w-full rounded-xl border bg-white
              placeholder:text-surface-400
              transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-offset-0
              disabled:bg-surface-50 disabled:text-surface-400 disabled:cursor-not-allowed
              ${sizeStyles[size]}
              ${leftIcon ? 'pl-10' : 'px-3.5'}
              ${rightIcon ? 'pr-10' : 'px-3.5'}
              ${
                error
                  ? 'border-danger-400 focus:border-danger-500 focus:ring-danger-200'
                  : 'border-surface-300 focus:border-primary-500 focus:ring-primary-200'
              }
            `}
            {...props}
          />

          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center text-surface-400">
              {rightIcon}
            </div>
          )}
        </div>

        {(error || helperText) && (
          <p
            className={`mt-1.5 text-xs ${
              error ? 'text-danger-600' : 'text-surface-500'
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

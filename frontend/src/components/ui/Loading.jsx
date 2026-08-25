/**
 * Loading spinner / skeleton with multiple display modes.
 *
 * @param {'spinner'|'dots'|'skeleton'|'pulse'} variant
 * @param {'sm'|'md'|'lg'|'xl'} size
 * @param {boolean} fullScreen — centers the loader in the viewport
 * @param {string} text — optional loading message
 */
const Loading = ({
  variant = 'spinner',
  size = 'md',
  fullScreen = false,
  text,
  className = '',
}) => {
  const spinnerSizes = {
    sm: 'h-5 w-5',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  };

  const Spinner = () => (
    <svg
      className={`animate-spin text-primary-600 ${spinnerSizes[size]}`}
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
  );

  const Dots = () => (
    <div className="flex items-center gap-1.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className={`
            rounded-full bg-primary-500 animate-pulse-soft
            ${size === 'sm' ? 'h-1.5 w-1.5' : size === 'lg' ? 'h-3 w-3' : 'h-2 w-2'}
          `}
          style={{ animationDelay: `${i * 200}ms` }}
        />
      ))}
    </div>
  );

  const Skeleton = () => (
    <div className="w-full space-y-3 animate-pulse">
      <div className="h-4 bg-surface-200 rounded-lg w-3/4" />
      <div className="h-4 bg-surface-200 rounded-lg w-full" />
      <div className="h-4 bg-surface-200 rounded-lg w-5/6" />
    </div>
  );

  const Pulse = () => (
    <div
      className={`rounded-full bg-primary-100 animate-pulse-soft ${spinnerSizes[size]}`}
    />
  );

  const components = { spinner: Spinner, dots: Dots, skeleton: Skeleton, pulse: Pulse };
  const Component = components[variant];

  const content = (
    <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
      <Component />
      {text && (
        <p className="text-sm text-surface-500 font-medium animate-pulse-soft">
          {text}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-40 flex items-center justify-center bg-white/60 backdrop-blur-sm">
        {content}
      </div>
    );
  }

  return content;
};

export default Loading;

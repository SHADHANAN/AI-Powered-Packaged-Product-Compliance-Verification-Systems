import { Card, Badge } from '../components/ui';

/**
 * Verification page — displays compliance check results.
 * Placeholder UI; verification logic will be added in later phases.
 */
const Verification = () => {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-surface-900">
          Verification Results
        </h1>
        <p className="mt-1 text-surface-500">
          View AI-powered compliance verification results.
        </p>
      </div>

      <Card variant="default">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-20 h-20 rounded-full bg-primary-50 flex items-center justify-center mb-5">
            <svg
              className="w-10 h-10 text-primary-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-surface-800 mb-2">
            No verifications yet
          </h3>
          <p className="text-surface-500 text-sm max-w-sm">
            Upload a product to begin the AI-powered compliance verification
            process.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Verification;

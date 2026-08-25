import { Card, Badge } from '../components/ui';

/**
 * History page — shows past verification history.
 * Placeholder UI; history data will be loaded in later phases.
 */
const History = () => {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-surface-900">
          Verification History
        </h1>
        <p className="mt-1 text-surface-500">
          Browse previous compliance verification records.
        </p>
      </div>

      <Card variant="default">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-20 h-20 rounded-full bg-surface-100 flex items-center justify-center mb-5">
            <svg
              className="w-10 h-10 text-surface-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-surface-800 mb-2">
            No history available
          </h3>
          <p className="text-surface-500 text-sm max-w-sm">
            Your verification history will be displayed here once you start
            scanning products.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default History;

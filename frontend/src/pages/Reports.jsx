import { Card, Badge } from '../components/ui';

/**
 * Reports page — lists generated compliance reports.
 * Placeholder UI; report logic will be added in later phases.
 */
const Reports = () => {
  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-surface-900">
            Reports
          </h1>
          <p className="mt-1 text-surface-500">
            View and download compliance reports.
          </p>
        </div>
        <Badge variant="neutral" size="lg">
          0 Reports
        </Badge>
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
                d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-surface-800 mb-2">
            No reports generated
          </h3>
          <p className="text-surface-500 text-sm max-w-sm">
            Reports will appear here after product compliance verifications are
            completed.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Reports;

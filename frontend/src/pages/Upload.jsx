import { Card, Button, Badge } from '../components/ui';

/**
 * Upload page — drag-and-drop area for product images/documents.
 * Placeholder UI; file upload logic will be added in later phases.
 */
const Upload = () => {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-surface-900">
          Upload Product
        </h1>
        <p className="mt-1 text-surface-500">
          Upload product images or documents for compliance verification.
        </p>
      </div>

      <Card variant="default">
        <div className="border-2 border-dashed border-surface-300 rounded-xl p-12 text-center hover:border-primary-400 hover:bg-primary-50/30 transition-all duration-300 cursor-pointer group">
          <div className="w-16 h-16 mx-auto rounded-full bg-primary-50 flex items-center justify-center mb-4 group-hover:bg-primary-100 transition-colors">
            <svg
              className="w-8 h-8 text-primary-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"
              />
            </svg>
          </div>
          <p className="text-surface-700 font-medium">
            Drag & drop files here, or{' '}
            <span className="text-primary-600 underline underline-offset-2">
              browse
            </span>
          </p>
          <p className="mt-2 text-xs text-surface-400">
            Supports JPG, PNG, PDF — Max 10 MB
          </p>
        </div>

        <div className="mt-6 flex justify-end">
          <Button variant="primary" disabled>
            Start Verification
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default Upload;

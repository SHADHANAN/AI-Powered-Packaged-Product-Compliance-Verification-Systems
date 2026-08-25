import { Card, Badge } from '../components/ui';

/**
 * Dashboard page — overview with stat cards and recent activity.
 * Placeholder UI; business logic will be added in later phases.
 */
const Dashboard = () => {
  const stats = [
    { label: 'Total Products', value: '—', variant: 'info', icon: '📦' },
    { label: 'Compliant', value: '—', variant: 'success', icon: '✅' },
    { label: 'Non-Compliant', value: '—', variant: 'danger', icon: '⚠️' },
    { label: 'Pending Review', value: '—', variant: 'warning', icon: '🕐' },
  ];

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-surface-900">
          Dashboard
        </h1>
        <p className="mt-1 text-surface-500">
          Overview of product compliance status and recent activity.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label} variant="elevated" hoverable>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-surface-500 font-medium">
                  {stat.label}
                </p>
                <p className="mt-2 text-3xl font-bold text-surface-900">
                  {stat.value}
                </p>
              </div>
              <span className="text-2xl">{stat.icon}</span>
            </div>
            <div className="mt-3">
              <Badge variant={stat.variant} size="sm" dot>
                Awaiting data
              </Badge>
            </div>
          </Card>
        ))}
      </div>

      {/* Recent Activity placeholder */}
      <Card
        variant="default"
        header={
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-surface-800">
              Recent Activity
            </h3>
            <Badge variant="neutral" size="sm">
              Coming soon
            </Badge>
          </div>
        }
      >
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="w-16 h-16 rounded-full bg-surface-100 flex items-center justify-center mb-4">
            <svg
              className="w-8 h-8 text-surface-400"
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
          <p className="text-surface-500 text-sm">
            No recent activity to display. Start by uploading a product for
            verification.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;

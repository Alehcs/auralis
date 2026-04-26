import { TrendingUp, Target, Clock, Database } from 'lucide-react';

export function MetricsCards() {
  const metrics = [
    {
      icon: Target,
      label: 'Model Accuracy',
      value: '94.2%',
      change: '+2.1%',
      trend: 'up',
      color: 'green'
    },
    {
      icon: TrendingUp,
      label: 'F1 Score',
      value: '0.917',
      change: '+0.03',
      trend: 'up',
      color: 'blue'
    },
    {
      icon: Clock,
      label: 'Last Update',
      value: '3 min',
      change: 'ago',
      trend: 'neutral',
      color: 'purple'
    },
    {
      icon: Database,
      label: 'Dataset Size',
      value: '847K',
      change: 'images',
      trend: 'neutral',
      color: 'orange'
    }
  ];

  const colorClasses = {
    green: 'from-green-500/10 to-green-500/5 border-green-500/20',
    blue: 'from-blue-500/10 to-blue-500/5 border-blue-500/20',
    purple: 'from-purple-500/10 to-purple-500/5 border-purple-500/20',
    orange: 'from-orange-500/10 to-orange-500/5 border-orange-500/20'
  };

  const iconColorClasses = {
    green: 'text-green-400',
    blue: 'text-blue-400',
    purple: 'text-purple-400',
    orange: 'text-orange-400'
  };

  return (
    <div className="grid grid-cols-4 gap-6 mb-6">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <div
            key={metric.label}
            className={`bg-gradient-to-br ${colorClasses[metric.color as keyof typeof colorClasses]} border rounded-xl p-6 hover:scale-105 transition-transform`}
          >
            <div className="flex items-center justify-between mb-4">
              <Icon className={`w-6 h-6 ${iconColorClasses[metric.color as keyof typeof iconColorClasses]}`} />
              {metric.trend === 'up' && (
                <span className="text-xs text-green-400 bg-green-500/20 px-2 py-0.5 rounded">
                  {metric.change}
                </span>
              )}
            </div>
            <p className="text-xs text-gray-400 mb-1">{metric.label}</p>
            <p className="text-3xl font-bold text-white mb-1">{metric.value}</p>
            {metric.trend === 'neutral' && (
              <p className="text-xs text-gray-500">{metric.change}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}

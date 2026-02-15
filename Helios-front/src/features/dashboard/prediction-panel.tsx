import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { TrendingUp, AlertTriangle } from 'lucide-react';

const predictionData = [
  { time: '00:00', actual: 45, predicted: 42, confidence: 85 },
  { time: '06:00', actual: 52, predicted: 55, confidence: 87 },
  { time: '12:00', actual: 68, predicted: 65, confidence: 89 },
  { time: '18:00', actual: 71, predicted: 73, confidence: 91 },
  { time: '24:00', actual: null, predicted: 82, confidence: 88 },
  { time: '30:00', actual: null, predicted: 95, confidence: 84 },
  { time: '36:00', actual: null, predicted: 108, confidence: 81 },
  { time: '48:00', actual: null, predicted: 115, confidence: 78 },
  { time: '72:00', actual: null, predicted: 124, confidence: 72 },
];

export function PredictionPanel() {
  return (
    <div className="bg-black/40 border border-white/10 rounded-xl p-6 mb-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">Solar Activity Forecast</h2>
          <p className="text-sm text-gray-400">Sunspot number prediction - Next 72 hours</p>
        </div>
        <div className="flex items-center space-x-2 px-4 py-2 bg-yellow-500/20 border border-yellow-500/30 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-yellow-400" />
          <span className="text-sm font-medium text-yellow-400">Medium Risk</span>
        </div>
      </div>

      <div className="h-80 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={predictionData}>
            <defs>
              <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
            <XAxis 
              dataKey="time" 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              label={{ value: 'Sunspot Number', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1f2937', 
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#fff'
              }}
            />
            <Area 
              type="monotone" 
              dataKey="actual" 
              stroke="#3b82f6" 
              strokeWidth={2}
              fill="url(#colorActual)"
              name="Actual"
            />
            <Area 
              type="monotone" 
              dataKey="predicted" 
              stroke="#f97316" 
              strokeWidth={2}
              strokeDasharray="5 5"
              fill="url(#colorPredicted)"
              name="Predicted"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-green-500/10 to-green-500/5 border border-green-500/20 rounded-lg p-4">
          <p className="text-xs text-gray-400 mb-2">24h Probability</p>
          <div className="flex items-end space-x-2">
            <p className="text-2xl font-bold text-green-400">Low</p>
            <p className="text-sm text-gray-500 mb-1">23%</p>
          </div>
        </div>

        <div className="bg-gradient-to-br from-yellow-500/10 to-yellow-500/5 border border-yellow-500/20 rounded-lg p-4">
          <p className="text-xs text-gray-400 mb-2">48h Probability</p>
          <div className="flex items-end space-x-2">
            <p className="text-2xl font-bold text-yellow-400">Medium</p>
            <p className="text-sm text-gray-500 mb-1">67%</p>
          </div>
        </div>

        <div className="bg-gradient-to-br from-red-500/10 to-red-500/5 border border-red-500/20 rounded-lg p-4">
          <p className="text-xs text-gray-400 mb-2">72h Probability</p>
          <div className="flex items-end space-x-2">
            <p className="text-2xl font-bold text-red-400">High</p>
            <p className="text-sm text-gray-500 mb-1">89%</p>
          </div>
        </div>
      </div>
    </div>
  );
}

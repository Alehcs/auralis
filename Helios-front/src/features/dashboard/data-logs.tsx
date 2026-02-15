import { CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export function DataLogs() {
  const logs = [
    {
      id: '1',
      pipeline: 'SDO/HMI Data Ingestion',
      status: 'success',
      time: '2m ago',
      duration: '1.2s',
      records: '1,247'
    },
    {
      id: '2',
      pipeline: 'Image Preprocessing',
      status: 'success',
      time: '2m ago',
      duration: '3.4s',
      records: '1,247'
    },
    {
      id: '3',
      pipeline: 'CNN Model Inference',
      status: 'running',
      time: 'Running',
      duration: '2.1s',
      records: '1,247'
    },
    {
      id: '4',
      pipeline: 'Feature Extraction',
      status: 'success',
      time: '5m ago',
      duration: '0.8s',
      records: '1,247'
    },
    {
      id: '5',
      pipeline: 'Prediction Generation',
      status: 'success',
      time: '5m ago',
      duration: '1.5s',
      records: '72'
    },
    {
      id: '6',
      pipeline: 'Data Quality Check',
      status: 'warning',
      time: '8m ago',
      duration: '0.3s',
      records: '1,247'
    }
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'running':
        return <Clock className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-400" />;
      default:
        return null;
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-500/10 border-green-500/20';
      case 'running':
        return 'bg-blue-500/10 border-blue-500/20';
      case 'warning':
        return 'bg-yellow-500/10 border-yellow-500/20';
      default:
        return 'bg-white/5 border-white/10';
    }
  };

  return (
    <div className="bg-black/40 border border-white/10 rounded-xl p-6">
      <h2 className="text-xl font-bold text-white mb-6">Pipeline Execution Logs</h2>
      
      <div className="overflow-hidden rounded-lg border border-white/10">
        <table className="w-full">
          <thead className="bg-white/5">
            <tr>
              <th className="text-left text-xs font-medium text-gray-400 px-4 py-3">Pipeline</th>
              <th className="text-left text-xs font-medium text-gray-400 px-4 py-3">Status</th>
              <th className="text-left text-xs font-medium text-gray-400 px-4 py-3">Execution Time</th>
              <th className="text-left text-xs font-medium text-gray-400 px-4 py-3">Duration</th>
              <th className="text-left text-xs font-medium text-gray-400 px-4 py-3">Records</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-white/5 transition-colors">
                <td className="px-4 py-3 text-sm text-white">{log.pipeline}</td>
                <td className="px-4 py-3">
                  <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full border ${getStatusBg(log.status)}`}>
                    {getStatusIcon(log.status)}
                    <span className="text-xs capitalize text-white">{log.status}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-400">{log.time}</td>
                <td className="px-4 py-3 text-sm text-gray-400">{log.duration}</td>
                <td className="px-4 py-3 text-sm text-gray-400">{log.records}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

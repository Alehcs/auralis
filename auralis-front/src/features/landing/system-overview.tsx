export function SystemOverview() {
  const specs = [
    {
      label: 'Model Architecture',
      value: 'Coronium V3 PRO',
      detail: 'Custom 4-stage residual CNN, ~207K params, dual-channel B+/B− · ONNX 86.6 KB'
    },
    {
      label: 'Data Source',
      value: 'NASA SDO/HMI',
      detail: 'Solar Dynamics Observatory magnetograms at 6173 Å'
    },
    {
      label: 'Pipeline Status',
      value: 'Local demo',
      detail: 'Inference runs against the processed dataset on localhost'
    },
    {
      label: 'Inference Target',
      value: 'Current index',
      detail: 'Estimates the activity index for the selected magnetogram'
    }
  ];

  return (
    <div className="px-6 py-16 bg-neutral-950 border-y border-neutral-800">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-semibold text-white mb-2">System Overview</h2>
          <p className="text-sm text-neutral-500">Core technical specifications</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {specs.map((spec) => (
            <div key={spec.label} className="bg-neutral-900 border border-neutral-800 p-5">
              <div className="text-[11px] text-neutral-500 mb-3 uppercase tracking-wide">
                {spec.label}
              </div>
              <div className="text-lg font-mono text-white mb-2">
                {spec.value}
              </div>
              <div className="text-xs text-neutral-400 leading-relaxed">
                {spec.detail}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

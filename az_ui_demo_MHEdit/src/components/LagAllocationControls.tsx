import React from 'react';

interface LagAllocationControlsProps {
  allocation: Record<'t' | 't1' | 't2' | 't3', number>;
  onUpdate: (field: 't' | 't1' | 't2' | 't3', value: number) => void;
}

const LABELS: Record<'t' | 't1' | 't2' | 't3', string> = {
  t: 'Current period (t)',
  t1: 'One lag (t-1)',
  t2: 'Two lag (t-2)',
  t3: 'Three lag (t-3)',
};

const LagAllocationControls: React.FC<LagAllocationControlsProps> = ({ allocation, onUpdate }) => {
  const total = allocation.t + allocation.t1 + allocation.t2 + allocation.t3;
  const isValid = Math.abs(total - 100) < 0.01;

  const fields: Array<'t' | 't1' | 't2' | 't3'> = ['t', 't1', 't2', 't3'];

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary space-y-4">
      <div>
        <h2 className="text-2xl font-semibold text-primary">Lag Allocation</h2>
        <p className="text-sm text-gray-500">Distribute influence across the four model lags. Values must total 100%.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {fields.map((field) => (
          <div key={field} className="space-y-1">
            <label className="block text-sm font-medium text-gray-600">{LABELS[field]}</label>
            <input
              type="number"
              min={0}
              max={100}
              step={1}
              value={allocation[field]}
              onChange={(event) => onUpdate(field, Number(event.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
        ))}
      </div>

      <div className={`p-3 rounded-lg border-l-4 ${isValid ? 'border-primary bg-gray-50' : 'border-red-500 bg-red-50'}`}>
        <p className="text-sm text-gray-600">
          Total Allocation: <strong className={isValid ? 'text-primary' : 'text-red-600'}>{total.toFixed(1)}%</strong> (must equal 100%).
        </p>
      </div>
    </div>
  );
};

export default LagAllocationControls;

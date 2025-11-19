import React, { useMemo } from 'react';
import { CostInputs as CostInputsType } from '../types';

interface CostInputsProps {
  inputs: CostInputsType;
  onInputChange: (field: keyof CostInputsType, value: number) => void;
  onLoadExternalData: () => void;
  isLoadingExternal?: boolean;
}

const CostInputs: React.FC<CostInputsProps> = ({ inputs, onInputChange, onLoadExternalData, isLoadingExternal = false }) => {
  const inputFields: Array<{ key: keyof CostInputsType; label: string; icon: string }> = [
    { key: 'labor', label: 'Labor', icon: '👥' },
    { key: 'capital', label: 'Capital', icon: '🏭' },
    { key: 'materials', label: 'Materials', icon: '📦' },
    { key: 'energy', label: 'Energy', icon: '⚡' },
    { key: 'other', label: 'Other', icon: '📋' },
  ];

  const totalWeight = useMemo(
    () => inputFields.reduce((sum, field) => sum + (inputs[field.key] || 0), 0),
    [inputs]
  );

  const isTotalValid = Math.abs(totalWeight - 100) < 0.01;

  const handleValueChange = (field: keyof CostInputsType, rawValue: string) => {
    const parsed = parseFloat(rawValue);
    const numericValue = Number.isFinite(parsed) ? parsed : 0;
    const clamped = Math.min(100, Math.max(0, numericValue));
    onInputChange(field, clamped);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-primary">Cost Inputs</h2>
        <div className="flex gap-3">
          <button
            onClick={onLoadExternalData}
            disabled={isLoadingExternal}
            className="px-4 py-2 bg-secondary text-white rounded-lg hover:bg-secondary/90 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span>📊</span>
            <span>{isLoadingExternal ? 'Loading...' : 'Load from External Data'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {inputFields.map((field) => (
          <div key={field.key} className="space-y-2">
            <label className="block text-sm font-medium text-gray-500">
              <span className="mr-2">{field.icon}</span>
              {field.label} (% Allocation)
            </label>
            <input
              type="number"
              min={0}
              max={100}
              step={0.1}
              value={inputs[field.key]}
              onChange={(e) => handleValueChange(field.key, e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white"
              placeholder="0 - 100"
            />
            <p className="text-xs text-gray-500">Directly enter the share of total cost pressure attributed to this category.</p>
          </div>
        ))}
      </div>

      <div
        className={`mt-6 p-4 rounded-lg border-l-4 ${
          isTotalValid ? 'border-primary bg-gray-50' : 'border-red-400 bg-red-50'
        }`}
      >
        <p className="text-sm text-gray-600">
          <strong className="text-primary">Total allocation:</strong>{' '}
          <span className={isTotalValid ? 'text-primary' : 'text-red-600'}>
            {totalWeight.toFixed(1)}%
          </span>{' '}
          (must equal 100%). Use the external data loader to auto-balance the latest market data, or enter your own mix manually.
        </p>
      </div>
    </div>
  );
};

export default CostInputs;


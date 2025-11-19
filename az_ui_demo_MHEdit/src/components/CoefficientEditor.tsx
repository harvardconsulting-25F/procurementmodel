import React from 'react';
import { ModelCoefficients, CoefficientLevel, numericToLevel, levelToNumeric } from '../types';

interface CoefficientEditorProps {
  coefficients: ModelCoefficients;
  onCoefficientChange: (field: keyof ModelCoefficients, value: number) => void;
  onResetToDefaults: () => void;
}

const CoefficientEditor: React.FC<CoefficientEditorProps> = ({
  coefficients,
  onCoefficientChange,
  onResetToDefaults,
}) => {
  const coefficientGroups = [
    {
      label: 'Current Period (t)',
      prefix: '',
      fields: [
        { key: 'labor_t' as keyof ModelCoefficients, label: 'Labor' },
        { key: 'capital_t' as keyof ModelCoefficients, label: 'Capital' },
        { key: 'materials_t' as keyof ModelCoefficients, label: 'Materials' },
        { key: 'energy_t' as keyof ModelCoefficients, label: 'Energy' },
        { key: 'other_t' as keyof ModelCoefficients, label: 'Other' },
      ],
    },
    {
      label: 'One Period Lag (t-1)',
      prefix: 't1',
      fields: [
        { key: 'labor_t1' as keyof ModelCoefficients, label: 'Labor' },
        { key: 'capital_t1' as keyof ModelCoefficients, label: 'Capital' },
        { key: 'materials_t1' as keyof ModelCoefficients, label: 'Materials' },
        { key: 'energy_t1' as keyof ModelCoefficients, label: 'Energy' },
        { key: 'other_t1' as keyof ModelCoefficients, label: 'Other' },
      ],
    },
    {
      label: 'Two Period Lag (t-2)',
      prefix: 't2',
      fields: [
        { key: 'labor_t2' as keyof ModelCoefficients, label: 'Labor' },
        { key: 'capital_t2' as keyof ModelCoefficients, label: 'Capital' },
        { key: 'materials_t2' as keyof ModelCoefficients, label: 'Materials' },
        { key: 'energy_t2' as keyof ModelCoefficients, label: 'Energy' },
        { key: 'other_t2' as keyof ModelCoefficients, label: 'Other' },
      ],
    },
    {
      label: 'Three Period Lag (t-3)',
      prefix: 't3',
      fields: [
        { key: 'labor_t3' as keyof ModelCoefficients, label: 'Labor' },
        { key: 'capital_t3' as keyof ModelCoefficients, label: 'Capital' },
        { key: 'materials_t3' as keyof ModelCoefficients, label: 'Materials' },
        { key: 'energy_t3' as keyof ModelCoefficients, label: 'Energy' },
        { key: 'other_t3' as keyof ModelCoefficients, label: 'Other' },
      ],
    },
  ];

  const handleLevelChange = (field: keyof ModelCoefficients, level: CoefficientLevel) => {
    const originalValue = coefficients[field];
    const numericValue = levelToNumeric(level, originalValue);
    onCoefficientChange(field, numericValue);
  };

  const getCurrentLevel = (field: keyof ModelCoefficients): CoefficientLevel => {
    return numericToLevel(coefficients[field]);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-primary">Model Coefficients</h2>
        <button
          onClick={onResetToDefaults}
          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
        >
          Reset to Defaults
        </button>
      </div>

      <div className="space-y-6">
        {coefficientGroups.map((group) => (
          <div key={group.label} className="border border-gray-200 rounded-lg p-4 border-l-4 border-l-primary">
            <h3 className="text-lg font-medium text-primary mb-4">{group.label}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {group.fields.map((field) => (
                <div key={field.key} className="space-y-2">
                  <label className="block text-sm font-medium text-gray-500">
                    {field.label}
                  </label>
                  <select
                    value={getCurrentLevel(field.key)}
                    onChange={(e) => handleLevelChange(field.key, e.target.value as CoefficientLevel)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white"
                  >
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-gray-100 rounded-lg border-l-4 border-primary">
        <p className="text-sm text-gray-500">
          <strong className="text-primary">Note:</strong> Adjust these coefficients to modify the model's sensitivity to different 
          input factors across different time periods. Changes will affect the price prediction.
        </p>
      </div>
    </div>
  );
};

export default CoefficientEditor;


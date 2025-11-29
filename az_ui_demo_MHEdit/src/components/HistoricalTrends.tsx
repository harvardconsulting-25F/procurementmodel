import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { LatestDataResponse } from '../types';

interface HistoricalTrendsProps {
  data: LatestDataResponse | null;
  months: number;
  onMonthsChange: (value: number) => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  labor: 'Labor',
  capital: 'Capital',
  materials: 'Materials',
  energy: 'Energy',
};

const HistoricalTrends: React.FC<HistoricalTrendsProps> = ({ data, months, onMonthsChange }) => {
  const history = data?.history || {};

  const charts = Object.keys(CATEGORY_LABELS).map((key) => {
    const entries = history[key] || [];
    const display = entries.slice(-months).map((entry) => ({
      date: entry.date || '',
      value: entry.pct_change ?? 0,
    }));
    return {
      key,
      label: CATEGORY_LABELS[key],
      points: display,
    };
  });

  return (
    <section className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary space-y-5">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-primary">Historical Input Trends</h2>
          <p className="text-sm text-gray-500">Slide to adjust how many months of history to visualize.</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-600">Months: {months}</label>
          <input
            type="range"
            min={3}
            max={12}
            value={months}
            onChange={(event) => onMonthsChange(Number(event.target.value))}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {charts.map((chart) => (
          <div key={chart.key} className="p-4 border rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-primary">{chart.label}</h3>
              <p className="text-xs text-gray-500">
                Last {Math.min(months, chart.points.length)} months
              </p>
            </div>
            {chart.points.length > 1 ? (
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chart.points} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(value) => value?.slice(0, 7) || ''} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
                    <Line type="monotone" dataKey="value" stroke="#8b1d2c" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-sm text-gray-400">Not enough history available.</p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
};

export default HistoricalTrends;

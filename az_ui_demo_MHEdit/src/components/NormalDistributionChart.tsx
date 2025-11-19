import React, { useMemo } from 'react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ReferenceLine } from 'recharts';
import { PredictionResult, PredictionSummary } from '../types';

interface NormalDistributionChartProps {
  prediction: PredictionResult | null;
  explanationText?: string;
  summary?: PredictionSummary | null;
}

const NormalDistributionChart: React.FC<NormalDistributionChartProps> = ({
  prediction,
  explanationText,
  summary,
}) => {
  const chartData = useMemo(() => {
    if (!prediction) {
      return [];
    }

    const safeStd = Math.max(prediction.stdDev, 0.0001);
    const safeMean = Math.max(0, prediction.mean);
    const minPrice = Math.max(0, prediction.min);
    const maxPrice = Math.max(minPrice + 0.0001, prediction.max);

    // Generate normal distribution data points
    const data: Array<{ price: number; probability: number }> = [];
    const numPoints = 200;
    const range = maxPrice - minPrice;
    const step = range / numPoints;

    for (let i = 0; i <= numPoints; i++) {
      const x = minPrice + i * step;
      // Normal distribution PDF: (1 / (σ * √(2π))) * e^(-0.5 * ((x - μ) / σ)²)
      const z = (x - safeMean) / safeStd;
      const probability = (1 / (safeStd * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * z * z);
      data.push({ price: x, probability });
    }

    return data;
  }, [prediction]);

  if (!prediction) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary">
        <h2 className="text-2xl font-semibold text-primary mb-4">Price Prediction Distribution</h2>
        
        {/* Explanation text */}
        {explanationText && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg border-l-4 border-primary">
            <p className="text-base text-gray-700 leading-relaxed">{explanationText}</p>
          </div>
        )}
        
        <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg">
          <p className="text-gray-500">Enter cost inputs and adjust coefficients to see prediction</p>
        </div>
      </div>
    );
  }

  const safeMean = Math.max(0, prediction.mean);
  const safeStd = Math.max(prediction.stdDev, 0.0001);
  const confidence95Min = Math.max(0, safeMean - 1.96 * safeStd);
  const confidence95Max = Math.max(confidence95Min, safeMean + 1.96 * safeStd);
  const confidence68Min = Math.max(0, safeMean - safeStd);
  const confidence68Max = Math.max(confidence68Min, safeMean + safeStd);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary">
      <h2 className="text-2xl font-semibold text-primary mb-4">Price Prediction Distribution</h2>

      {summary?.headline && (
        <div className="mb-4 p-4 bg-primary/5 rounded-lg border border-primary/40">
          <p className="text-primary font-semibold">{summary.headline}</p>
        </div>
      )}
      
      {/* Explanation text */}
      {explanationText && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg border-l-4 border-primary">
          <p className="text-base text-gray-700 leading-relaxed">{explanationText}</p>
        </div>
      )}
      
      <div className="mb-6">
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorProbability" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#109B9D" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#109B9D" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#D5D5D5" />
            <XAxis 
              dataKey="price" 
              label={{ value: 'Price Change (%)', position: 'insideBottom', offset: -5 }}
              stroke="#7F7F7F"
            />
            <YAxis 
              label={{ value: 'Probability Density', angle: -90, position: 'insideLeft' }}
              stroke="#7F7F7F"
            />
            <Tooltip 
              formatter={(value: number) => [value.toFixed(4), 'Probability']}
              labelFormatter={(label) => `Price: ${Number(label).toFixed(2)}%`}
            />
            <ReferenceLine 
              x={prediction.mean} 
              stroke="#A82626" 
              strokeWidth={2} 
              strokeDasharray="5 5"
              label={{ value: "Mean", position: "top", fill: "#A82626", fontSize: 12 }}
            />
            <Area
              type="monotone"
              dataKey="probability"
              stroke="#109B9D"
              strokeWidth={2}
              fill="url(#colorProbability)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        <div className="bg-gray-100 p-4 rounded-lg border-l-4 border-primary">
          <p className="text-sm text-gray-500 font-medium">Mean (Expected)</p>
          <p className="text-2xl font-bold text-primary">{safeMean.toFixed(2)}%</p>
        </div>
        <div className="bg-gray-100 p-4 rounded-lg border-l-4 border-primary">
          <p className="text-sm text-gray-500 font-medium">68% Confidence Range</p>
          <p className="text-lg font-semibold text-primary">
            {confidence68Min.toFixed(2)}% to {confidence68Max.toFixed(2)}%
          </p>
        </div>
        <div className="bg-gray-100 p-4 rounded-lg border-l-4 border-primary">
          <p className="text-sm text-gray-500 font-medium">95% Confidence Range</p>
          <p className="text-lg font-semibold text-primary">
            {confidence95Min.toFixed(2)}% to {confidence95Max.toFixed(2)}%
          </p>
        </div>
        <div className="bg-gray-100 p-4 rounded-lg border-l-4 border-primary">
          <p className="text-sm text-gray-500 font-medium">Standard Deviation</p>
          <p className="text-2xl font-bold text-primary">{prediction.stdDev.toFixed(2)}%</p>
        </div>
      </div>

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <div className="p-4 rounded-lg border border-gray-200 bg-gray-50">
            <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">Price Change Level</p>
            <p className="text-lg font-bold text-primary mt-1">{summary.priceLevelLabel}</p>
            <p className="text-sm text-gray-600 mt-2">{summary.priceLevelDescription}</p>
          </div>
          <div className="p-4 rounded-lg border border-gray-200 bg-gray-50">
            <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">Confidence</p>
            <p className="text-lg font-bold text-primary mt-1">{summary.confidenceLabel}</p>
            <p className="text-sm text-gray-600 mt-2">{summary.confidenceDescription}</p>
          </div>
          <div className="p-4 rounded-lg border border-gray-200 bg-gray-50">
            <p className="text-xs font-semibold uppercase text-gray-500 tracking-wide">Trend Insight</p>
            <p className="text-lg font-bold text-primary mt-1">{summary.trendLabel}</p>
            <p className="text-sm text-gray-600 mt-2">{summary.trendDescription}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default NormalDistributionChart;


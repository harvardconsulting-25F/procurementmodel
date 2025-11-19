export interface CostInputs {
  labor: number;
  capital: number;
  materials: number;
  energy: number;
  other: number;
}

export interface ModelCoefficients {
  // Current period (t)
  labor_t: number;
  capital_t: number;
  materials_t: number;
  energy_t: number;
  other_t: number;
  // One period lag (t-1)
  labor_t1: number;
  capital_t1: number;
  materials_t1: number;
  energy_t1: number;
  other_t1: number;
  // Two period lag (t-2)
  labor_t2: number;
  capital_t2: number;
  materials_t2: number;
  energy_t2: number;
  other_t2: number;
  // Three period lag (t-3)
  labor_t3: number;
  capital_t3: number;
  materials_t3: number;
  energy_t3: number;
  other_t3: number;
}

export type CoefficientLevel = 'high' | 'medium' | 'low';

export interface CoefficientLevels {
  high: number;
  medium: number;
  low: number;
}

export const COEFFICIENT_LEVELS: CoefficientLevels = {
  high: 0.8,
  medium: 0.6,
  low: 0.2,
};

// Helper function to map numeric value to closest level (for coefficients)
export const numericToLevel = (value: number): CoefficientLevel => {
  const absValue = Math.abs(value);
  if (absValue >= 0.7) return 'high';
  if (absValue >= 0.4) return 'medium';
  return 'low';
};

// Helper function to map level to numeric value (preserves sign for coefficients)
export const levelToNumeric = (level: CoefficientLevel, originalValue: number): number => {
  const sign = originalValue >= 0 ? 1 : -1;
  return sign * COEFFICIENT_LEVELS[level];
};

export interface PredictionResult {
  mean: number;
  stdDev: number;
  min: number;
  max: number;
}

export interface LatestDataResponse {
  labor: number;
  capital: number;
  materials: number;
  energy: number;
  other: number;
  full_data?: Record<string, number[]>;
}

export interface PredictionSummary {
  headline: string;
  priceLevelLabel: string;
  priceLevelDescription: string;
  confidenceLabel: string;
  confidenceDescription: string;
  trendLabel: string;
  trendDescription: string;
}


import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import CostInputs from './components/CostInputs';
import CoefficientEditor from './components/CoefficientEditor';
import NormalDistributionChart from './components/NormalDistributionChart';
import Logo from './components/Logo';
import ModelOverview from './components/ModelOverview';
type TabKey = 'dashboard' | 'model';
import {
  CostInputs as CostInputsType,
  ModelCoefficients,
  PredictionResult,
  PredictionSummary,
  LatestDataResponse,
  numericToLevel,
} from './types';

// Default coefficients based on the equation structure
const DEFAULT_COEFFICIENTS: ModelCoefficients = {
  // Current period (t)
  labor_t: 0.14,
  capital_t: 0.07,
  materials_t: 0.07,
  energy_t: 0.04,
  other_t: 0.06,
  // One period lag (t-1)
  labor_t1: 0.07,
  capital_t1: 0.07,
  materials_t1: 0.07,
  energy_t1: 0.08,
  other_t1: 0.06,
  // Two period lag (t-2) - negative
  labor_t2: -0.05,
  capital_t2: -0.01,
  materials_t2: -0.04,
  energy_t2: -0.08,
  other_t2: -0.02,
  // Three period lag (t-3) - negative (except capital which becomes positive)
  labor_t3: -0.06,
  capital_t3: 0.11, // Note: becomes positive due to double negative
  materials_t3: -0.04,
  energy_t3: -0.08,
  other_t3: -0.02,
};

const DEFAULT_LOCAL_API = 'http://localhost:5001';

const sanitizeUrl = (value: string): string => value.replace(/\/+$/, '');

const getInitialApiBaseUrl = (): string => {
  const envUrl = (import.meta.env.VITE_API_URL as string | undefined)?.trim();
  if (envUrl) {
    return sanitizeUrl(envUrl);
  }
  return DEFAULT_LOCAL_API;
};

const INITIAL_WEIGHTS: CostInputsType = {
  labor: 20,
  capital: 20,
  materials: 20,
  energy: 20,
  other: 20,
};

const CATEGORY_ORDER: Array<keyof CostInputsType> = ['labor', 'capital', 'materials', 'energy', 'other'];
const PERCENT_TOLERANCE = 0.01;

const getTotalWeight = (inputs: CostInputsType): number =>
  CATEGORY_ORDER.reduce((sum, key) => sum + (inputs[key] || 0), 0);

const weightsAreValid = (inputs: CostInputsType): boolean =>
  Math.abs(getTotalWeight(inputs) - 100) <= PERCENT_TOLERANCE;

const normalizeWeightsFromFullData = (data: LatestDataResponse): CostInputsType => {
  const allocations: CostInputsType = { labor: 0, capital: 0, materials: 0, energy: 0, other: 0 };
  const seriesValues = CATEGORY_ORDER.map((key) => {
    const series = data.full_data?.[key];
    if (Array.isArray(series) && series.length) {
      return Math.abs(series[series.length - 1]);
    }
    return Math.abs(data[key] ?? 0);
  });

  const total = seriesValues.reduce((sum, val) => sum + val, 0);
  if (total === 0) {
    return { ...INITIAL_WEIGHTS };
  }

  CATEGORY_ORDER.forEach((key, index) => {
    allocations[key] = parseFloat(((seriesValues[index] / total) * 100).toFixed(2));
  });

  const roundingDiff = 100 - getTotalWeight(allocations);
  allocations.other = parseFloat((allocations.other + roundingDiff).toFixed(2));
  return allocations;
};

const classifyPriceChange = (mean: number) => {
  if (mean < 2) {
    return {
      label: 'Low (0-2%)',
      description: 'Minor price movement. Adjustments can be monitored through business-as-usual cadence.',
    };
  }
  if (mean < 8) {
    return {
      label: 'Medium (2-8%)',
      description: 'Meaningful shift that may warrant supplier negotiations or hedging conversations.',
    };
  }
  return {
    label: 'High (8%+ / High-Medium band)',
    description: 'Material change expected. Consider proactive actions with suppliers and downstream pricing.',
  };
};

const classifyConfidence = (range: number) => {
  if (range <= 4) {
    return {
      label: 'High confidence (narrow)',
      description: 'Distribution is tight (≤4 percentage points), indicating a concentrated projection.',
    };
  }
  if (range <= 8) {
    return {
      label: 'Medium confidence',
      description: 'Range is moderate. Keep monitoring inputs; additional data can sharpen the forecast.',
    };
  }
  return {
    label: 'Low confidence (wide)',
    description: 'Wide distribution suggests volatility—treat this projection as directional, not precise.',
  };
};

const describeTrend = (delta: number | null, mean: number) => {
  if (delta === null) {
    return {
      label: 'Baseline established',
      description: 'First run with the current allocation. Use future recalculations to track momentum.',
    };
  }
  if (delta > 0.5) {
    return {
      label: 'Momentum building',
      description: `Average price change increased by ${delta.toFixed(2)} pts since the last scenario, signaling acceleration.`,
    };
  }
  if (delta < -0.5) {
    return {
      label: 'Momentum cooling',
      description: `Average price change fell by ${Math.abs(delta).toFixed(2)} pts, indicating easing pressure.`,
    };
  }
  return {
    label: 'Holding steady',
    description: `Changes were within ±0.5 pts of the prior run. The ${mean.toFixed(2)}% outlook remains stable.`,
  };
};

// Calculate prediction using the API
const calculatePrediction = async (
  apiBaseUrl: string,
  inputs: CostInputsType,
  coefficients: ModelCoefficients
): Promise<PredictionResult | null> => {
  try {
    if (!apiBaseUrl) {
      throw new Error('API base URL is not configured');
    }

    // Send coefficients as-is (UI stores them with correct signs)
    const apiCoefficients = {
      labor_t: coefficients.labor_t,
      capital_t: coefficients.capital_t,
      materials_t: coefficients.materials_t,
      energy_t: coefficients.energy_t,
      other_t: coefficients.other_t,
      labor_t1: coefficients.labor_t1,
      capital_t1: coefficients.capital_t1,
      materials_t1: coefficients.materials_t1,
      energy_t1: coefficients.energy_t1,
      other_t1: coefficients.other_t1,
      labor_t2: coefficients.labor_t2,
      capital_t2: coefficients.capital_t2,
      materials_t2: coefficients.materials_t2,
      energy_t2: coefficients.energy_t2,
      other_t2: coefficients.other_t2,
      labor_t3: coefficients.labor_t3,
      capital_t3: coefficients.capital_t3,
      materials_t3: coefficients.materials_t3,
      energy_t3: coefficients.energy_t3,
      other_t3: coefficients.other_t3,
    };

    const response = await fetch(`${apiBaseUrl}/api/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        labor: inputs.labor,
        capital: inputs.capital,
        materials: inputs.materials,
        energy: inputs.energy,
        other: inputs.other,
        coefficients: apiCoefficients,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to calculate prediction');
    }

    const data = await response.json();
    return {
      mean: data.mean,
      stdDev: data.stdDev,
      min: data.min,
      max: data.max,
    };
  } catch (error) {
    console.error('Error calculating prediction:', error);
    // Return null on error - UI will handle gracefully
    return null;
  }
};

// Load external data from the API
const loadExternalData = async (apiBaseUrl: string): Promise<LatestDataResponse> => {
  try {
    if (!apiBaseUrl) {
      throw new Error('API base URL is not configured');
    }

    const response = await fetch(`${apiBaseUrl}/api/data/latest`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to load external data');
    }

    const data = await response.json();
    return {
      labor: data.labor || 0,
      capital: data.capital || 0,
      materials: data.materials || 0,
      energy: data.energy || 0,
      other: data.other || 0,
      full_data: data.full_data || {},
    };
  } catch (error) {
    console.error('Error loading external data:', error);
    throw error;
  }
};

function App() {
  const [costInputs, setCostInputs] = useState<CostInputsType>({ ...INITIAL_WEIGHTS });

  const [coefficients, setCoefficients] = useState<ModelCoefficients>(DEFAULT_COEFFICIENTS);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [isLoadingExternal, setIsLoadingExternal] = useState(false);
  const [isCalculating, setIsCalculating] = useState(false);
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard');
  const [trendDelta, setTrendDelta] = useState<number | null>(null);
  const [apiBaseUrl] = useState<string>(() => getInitialApiBaseUrl());
  const [apiStatus, setApiStatus] = useState<'checking' | 'ok' | 'error'>('checking');
  const [apiStatusMessage, setApiStatusMessage] = useState<string>('Checking connection...');
  const previousMeanRef = useRef<number | null>(null);

  useEffect(() => {
    if (!apiBaseUrl) {
      setApiStatus('error');
      setApiStatusMessage('API URL not configured.');
      return;
    }

    setApiStatus('checking');
    setApiStatusMessage('Checking connection...');

    const controller = new AbortController();
    let cancelled = false;

    fetch(`${apiBaseUrl}/api/health`, { signal: controller.signal })
      .then((response) => {
        if (cancelled) return;
        if (response.ok) {
          setApiStatus('ok');
          setApiStatusMessage('Connected to API');
        } else {
          setApiStatus('error');
          setApiStatusMessage(`API health check failed (${response.status})`);
        }
      })
      .catch((error) => {
        if (cancelled) return;
        setApiStatus('error');
        setApiStatusMessage(error.message || 'Unable to reach API');
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [apiBaseUrl]);

  const totalWeight = useMemo(() => getTotalWeight(costInputs), [costInputs]);
  const weightsValid = useMemo(() => weightsAreValid(costInputs), [costInputs]);

  const resetPredictionState = useCallback(() => {
    setPrediction(null);
    setTrendDelta(null);
    previousMeanRef.current = null;
  }, []);


  const runPrediction = useCallback(
    async (inputsSnapshot: CostInputsType, coefficientSnapshot: ModelCoefficients) => {
      if (!weightsAreValid(inputsSnapshot) || !apiBaseUrl) {
        resetPredictionState();
        if (!apiBaseUrl) {
          console.warn('API base URL is not configured. Prediction skipped.');
        }
        return;
      }

      setIsCalculating(true);
      try {
        const newPrediction = await calculatePrediction(apiBaseUrl, inputsSnapshot, coefficientSnapshot);
        setPrediction(newPrediction);
        if (newPrediction) {
          const previousMean = previousMeanRef.current;
          setTrendDelta(previousMean !== null ? newPrediction.mean - previousMean : null);
          previousMeanRef.current = newPrediction.mean;
        } else {
          resetPredictionState();
        }
      } catch (error) {
        console.error('Error calculating prediction:', error);
        resetPredictionState();
      } finally {
        setIsCalculating(false);
      }
    },
    [apiBaseUrl, resetPredictionState]
  );

  const handleInputChange = useCallback(
    (field: keyof CostInputsType, value: number) => {
      const sanitizedValue = Number.isFinite(value) ? Math.min(100, Math.max(0, value)) : 0;
      const newInputs = { ...costInputs, [field]: sanitizedValue };
      setCostInputs(newInputs);

      if (weightsAreValid(newInputs)) {
        runPrediction(newInputs, coefficients);
      } else {
        resetPredictionState();
      }
    },
    [costInputs, coefficients, resetPredictionState, runPrediction]
  );

  const handleCoefficientChange = useCallback(
    (field: keyof ModelCoefficients, value: number) => {
      const newCoefficients = { ...coefficients, [field]: value };
      setCoefficients(newCoefficients);

      if (weightsValid) {
        runPrediction(costInputs, newCoefficients);
      }
    },
    [coefficients, costInputs, weightsValid, runPrediction]
  );

  const handleResetCoefficients = useCallback(() => {
    setCoefficients(DEFAULT_COEFFICIENTS);
    if (weightsValid) {
      runPrediction(costInputs, DEFAULT_COEFFICIENTS);
    }
  }, [costInputs, weightsValid, runPrediction]);

  const handleLoadExternalData = useCallback(async () => {
    if (!apiBaseUrl) {
      alert('Enter the API base URL to load external data.');
      return;
    }

    setIsLoadingExternal(true);
    try {
      const externalPayload = await loadExternalData(apiBaseUrl);
      const normalizedWeights = normalizeWeightsFromFullData(externalPayload);
      setCostInputs(normalizedWeights);
      if (weightsAreValid(normalizedWeights)) {
        await runPrediction(normalizedWeights, coefficients);
      } else {
        resetPredictionState();
      }
    } catch (error) {
      console.error('Error loading external data:', error);
      const extraMessage = error instanceof Error ? ` Details: ${error.message}` : '';
      alert(`Failed to load external data. Please make sure the API server is reachable at ${apiBaseUrl}.${extraMessage}`);
    } finally {
      setIsLoadingExternal(false);
    }
  }, [apiBaseUrl, coefficients, runPrediction, resetPredictionState]);

  // Generate explanatory text for price prediction
  const explanationText = useMemo(() => {
    if (!weightsValid) {
      return `Allocate 100% across labor, capital, materials, energy, and other (currently ${totalWeight.toFixed(
        1
      )}%).`;
    }
    if (!prediction) {
      return 'Enter percentage allocations and adjust coefficient levels to see a price prediction and explanation.';
    }

    // Calculate contributions: contribution = cost_change * coefficient
    // We need to sum contributions across all time periods for each input type
    const getContribution = (inputKey: keyof CostInputsType, coeffPrefix: string) => {
      const inputValue = costInputs[inputKey];
      const coeffSum = (coefficients[`${coeffPrefix}_t` as keyof ModelCoefficients] || 0) +
                       (coefficients[`${coeffPrefix}_t1` as keyof ModelCoefficients] || 0) +
                       (coefficients[`${coeffPrefix}_t2` as keyof ModelCoefficients] || 0) +
                       (coefficients[`${coeffPrefix}_t3` as keyof ModelCoefficients] || 0);
      return inputValue * coeffSum;
    };

    const contributions = {
      labor: getContribution('labor', 'labor'),
      capital: getContribution('capital', 'capital'),
      materials: getContribution('materials', 'materials'),
      energy: getContribution('energy', 'energy'),
      other: getContribution('other', 'other'),
    };

    // Get absolute contributions and sort by magnitude
    const contributionEntries = Object.entries(contributions).map(([key, value]) => ({
      key: key as keyof typeof contributions,
      name: key.charAt(0).toUpperCase() + key.slice(1),
      contribution: value,
      absContribution: Math.abs(value),
      inputValue: costInputs[key as keyof CostInputsType],
      avgCoeff: Math.abs(
        ((coefficients[`${key}_t` as keyof ModelCoefficients] || 0) +
         (coefficients[`${key}_t1` as keyof ModelCoefficients] || 0) +
         (coefficients[`${key}_t2` as keyof ModelCoefficients] || 0) +
         (coefficients[`${key}_t3` as keyof ModelCoefficients] || 0)) / 4
      ),
    }));

    // Sort by absolute contribution (descending)
    contributionEntries.sort((a, b) => b.absContribution - a.absContribution);

    // Identify top contributors (at least 10% of the mean or top 2)
    const topContributors = contributionEntries
      .filter(entry => entry.absContribution > Math.abs(prediction.mean) * 0.1)
      .slice(0, 2);

    // Build explanation text using the requested template format
    const direction = prediction.mean >= 0 ? 'increase' : 'decrease';
    const absMean = Math.abs(prediction.mean);
    
    // Get importance explanation based on magnitude of change
    const getImportanceExplanation = (meanChange: number): string => {
      const absChange = Math.abs(meanChange);
      if (absChange >= 30) {
        return 'this represents a significant cost shock that could substantially impact procurement budgets and pricing strategies.';
      } else if (absChange >= 15) {
        return 'this change is substantial enough to require procurement team attention and may necessitate contract renegotiations.';
      } else if (absChange >= 5) {
        return 'this moderate change should be monitored closely as it affects overall cost structure and profitability margins.';
      } else {
        return 'while relatively modest, this change accumulates over time and should be factored into long-term planning.';
      }
    };
    
    if (topContributors.length === 0) {
      return `${absMean.toFixed(1)}% ${direction} in the predicted price relative to the baseline. ${getImportanceExplanation(prediction.mean)}`;
    } else if (topContributors.length === 1) {
      const contributor = topContributors[0];
      const level = numericToLevel(contributor.avgCoeff);
      const changeWord = contributor.inputValue >= 0 ? 'higher' : 'lower';
      const inputChange = Math.abs(contributor.inputValue);
      
      return `${absMean.toFixed(1)}% ${direction} because ${contributor.name.toLowerCase()} costs created a supply shock, with ${changeWord} ${contributor.name.toLowerCase()} costs increasing by ${inputChange.toFixed(1)}% and weighted at ${level} level (${(contributor.avgCoeff * 100).toFixed(0)}% coefficient weight) in the model. This is important because ${getImportanceExplanation(prediction.mean)}`;
    } else {
      const contributor1 = topContributors[0];
      const contributor2 = topContributors[1];
      const level1 = numericToLevel(contributor1.avgCoeff);
      const level2 = numericToLevel(contributor2.avgCoeff);
      const changeWord1 = contributor1.inputValue >= 0 ? 'higher' : 'lower';
      const changeWord2 = contributor2.inputValue >= 0 ? 'higher' : 'lower';
      const inputChange1 = Math.abs(contributor1.inputValue);
      const inputChange2 = Math.abs(contributor2.inputValue);
      
      return `${absMean.toFixed(1)}% ${direction} because ${contributor1.name.toLowerCase()} costs created the primary supply shock, with ${changeWord1} ${contributor1.name.toLowerCase()} costs increasing by ${inputChange1.toFixed(1)}% weighted at ${level1} level (${(contributor1.avgCoeff * 100).toFixed(0)}% coefficient weight), along with ${changeWord2} ${contributor2.name.toLowerCase()} costs (${inputChange2.toFixed(1)}% change, ${level2} weight). This is important because ${getImportanceExplanation(prediction.mean)}`;
    }
  }, [prediction, costInputs, coefficients, weightsValid, totalWeight]);

  const predictionSummary = useMemo<PredictionSummary | null>(() => {
    if (!prediction) {
      return null;
    }

    const meanValue = Math.max(0, prediction.mean);
    const priceBand = classifyPriceChange(meanValue);
    const confidenceBand = classifyConfidence(Math.max(0, prediction.max - prediction.min));
    const trendBand = describeTrend(trendDelta, meanValue);

    return {
      headline: `Model projects ${meanValue.toFixed(2)}% price change.`,
      priceLevelLabel: priceBand.label,
      priceLevelDescription: priceBand.description,
      confidenceLabel: confidenceBand.label,
      confidenceDescription: confidenceBand.description,
      trendLabel: trendBand.label,
      trendDescription: trendBand.description,
    };
  }, [prediction, trendDelta]);

  const apiStatusColor =
    apiStatus === 'ok' ? 'text-green-600' : apiStatus === 'checking' ? 'text-amber-600' : 'text-red-600';
  const externalLoadEnabled = Boolean(apiBaseUrl) && apiStatus === 'ok';
  const externalLoadHint =
    apiStatus === 'checking'
      ? 'Validating API connection...'
      : apiStatus === 'error'
        ? 'API unreachable. Double-check your deployment.'
        : undefined;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-md border-b-4 border-primary">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Logo />
              <div className="border-l-4 border-primary pl-6">
                <h1 className="text-2xl font-bold text-primary">Procurement Model</h1>
                <p className="text-gray-400 text-sm mt-1">Biological Resin Process - Price Prediction</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-400">Procurement Manager Dashboard</p>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-white border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-6">
          <div className="flex gap-3 py-3">
            {[
              { key: 'dashboard', label: 'Forecast Dashboard' },
              { key: 'model', label: 'Model Insights' },
            ].map((tab) => {
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as TabKey)}
                  className={`flex-1 py-2 text-sm font-semibold rounded-lg border transition-all duration-200 ${
                    isActive
                      ? 'bg-primary text-white border-primary shadow-sm'
                      : 'bg-gray-50 text-gray-500 border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {activeTab === 'dashboard' ? (
          <div className="space-y-8">
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary">
              <div className="flex flex-col gap-2">
                <h2 className="text-xl font-semibold text-primary">API Connection</h2>
                <p className={`text-sm font-semibold ${apiStatusColor}`}>
                  {apiStatusMessage}
                  {apiBaseUrl ? ` · ${apiBaseUrl}` : ''}
                </p>
                <p className="text-xs text-gray-500">
                  Status automatically reflects the configured backend (set via `VITE_API_URL` during build).
                </p>
              </div>
            </div>

            {/* Cost Inputs Section */}
            <CostInputs
              inputs={costInputs}
              onInputChange={handleInputChange}
              onLoadExternalData={handleLoadExternalData}
              isLoadingExternal={isLoadingExternal}
              externalLoadEnabled={externalLoadEnabled}
              externalLoadHint={externalLoadHint}
            />

            {/* Coefficient Editor Section */}
            <CoefficientEditor
              coefficients={coefficients}
              onCoefficientChange={handleCoefficientChange}
              onResetToDefaults={handleResetCoefficients}
            />

            {/* Prediction Visualization Section */}
            {isCalculating && (
              <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary">
                <p className="text-center text-gray-500">Calculating prediction...</p>
              </div>
            )}
            <NormalDistributionChart
              prediction={prediction}
              explanationText={explanationText}
              summary={predictionSummary}
            />
          </div>
        ) : (
          <div className="space-y-8">
            <ModelOverview />
          </div>
        )}
      </main>

    </div>
  );
}

export default App;

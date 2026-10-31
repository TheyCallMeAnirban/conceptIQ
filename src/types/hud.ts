export interface CognitiveVector {
  id: string;
  label: string;
  value: number; // 0 - 100
  historicalValue: number;
  velocity: number; // e.g. +1.4% / cycle
  decayRate: number; // % / hour
  status: 'nominal' | 'divergent' | 'calibrating';
}

export interface ModuleTrack {
  id: string;
  code: string;
  title: string;
  domain: string;
  status: 'nominal' | 'active' | 'review_required' | 'locked';
  mastery: number; // 0 - 100%
  retention: number; // 0 - 100%
  activeConcept: string;
  problemPrompt: {
    title: string;
    description: string;
    systemEquation: string;
    parameterName: string;
    parameterUnit: string;
    currentValue: number;
    targetMin: number;
    targetMax: number;
    nominalTarget: number;
    tolerance: number;
    contextExplanation: string;
    socraticHints: string[];
    options?: {
      id: string;
      label: string;
      isNominal: boolean;
      explanation: string;
    }[];
  };
}

export interface TelemetryLog {
  id: string;
  timestamp: string;
  line: number;
  channel: string;
  type: 'nominal' | 'warning' | 'info' | 'critical';
  message: string;
}

export interface SessionMetrics {
  masteryVelocity: number; // e.g. +4.2 deg/hr or %/hr
  comprehensionBandwidth: number; // e.g. 84.6%
  retentionCurve: number; // e.g. 91.2%
  neuralFocusDrift: number; // e.g. 0.04 rad
  totalCycles: number;
  elapsedSeconds: number;
}

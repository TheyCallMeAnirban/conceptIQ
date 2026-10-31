/**
 * Pure mathematical and telemetry calculations for the Cyber-Physical Tutor.
 * Decoupled from UI components for high reliability and fast unit testing.
 */

export interface RadarPoint {
  x: number;
  y: number;
  id: string;
  label: string;
  value: number;
}

/**
 * Calculates (x, y) coordinates for a multi-axis spider / radar chart.
 */
export function calculateSpiderRadarVertices(
  vectors: Array<{ id: string; label: string; value: number }>,
  radius: number,
  center: { x: number; y: number }
): RadarPoint[] {
  const count = vectors.length;
  if (count === 0) return [];

  return vectors.map((vec, i) => {
    // Start at top (-PI/2) and rotate clockwise
    const angle = (i * 2 * Math.PI) / count - Math.PI / 2;
    const normalizedVal = Math.max(0, Math.min(100, vec.value)) / 100;
    const r = radius * normalizedVal;
    return {
      x: Number((center.x + r * Math.cos(angle)).toFixed(2)),
      y: Number((center.y + r * Math.sin(angle)).toFixed(2)),
      id: vec.id,
      label: vec.label,
      value: vec.value,
    };
  });
}

/**
 * Evaluates a learner's parameter tuning against nominal cyber-physical targets.
 */
export function evaluateStateVectorResponse(
  userVal: number,
  nominalTarget: number,
  tolerance: number
): { isNominal: boolean; deviation: number; score: number; statusMsg: string } {
  const deviation = Number(Math.abs(userVal - nominalTarget).toFixed(4));
  const isNominal = deviation <= tolerance;

  // Score decreases non-linearly with deviation
  const normalizedDev = tolerance === 0 ? 0 : deviation / (tolerance * 2.5);
  const score = Math.max(0, Math.min(100, Number((100 * Math.exp(-normalizedDev * 0.8)).toFixed(1))));

  let statusMsg = 'NOMINAL SYSTEM COUPLING';
  if (!isNominal) {
    if (userVal < nominalTarget) {
      statusMsg = 'UNDER-DAMPED OSCILLATION / GAIN DEFICIT';
    } else {
      statusMsg = 'OVER-SATURATED DIVERGENCE / BOUNDARY BREACH';
    }
  }

  return {
    isNominal,
    deviation,
    score,
    statusMsg,
  };
}

/**
 * Computes comprehension bandwidth based on correct response ratio, response latency, and complexity.
 */
export function calculateComprehensionBandwidth(
  accuracyRate: number, // 0 - 1
  avgLatencyMs: number,
  targetLatencyMs: number = 3000
): number {
  const boundedAccuracy = Math.max(0, Math.min(1, accuracyRate));
  const latencyFactor = Math.min(1.2, targetLatencyMs / Math.max(avgLatencyMs, 500));
  const rawBandwidth = boundedAccuracy * 85 + latencyFactor * 15;
  return Number(Math.max(10, Math.min(99.9, rawBandwidth)).toFixed(1));
}

/**
 * Ebbinghaus retention decay based on elapsed hours and stability coefficient.
 */
export function calculateRetentionDecay(
  initialMastery: number,
  elapsedHours: number,
  stability: number = 24
): number {
  if (elapsedHours <= 0) return Math.min(100, Math.max(0, initialMastery));
  // R = e^(-t/S)
  const decayMultiplier = Math.exp(-elapsedHours / Math.max(stability, 1));
  const retained = initialMastery * (0.4 + 0.6 * decayMultiplier);
  return Number(Math.max(5, Math.min(100, retained)).toFixed(1));
}

/**
 * Mastery velocity in percentage points per session hour.
 */
export function calculateMasteryVelocity(
  scoreDeltas: number[],
  timeDeltaHours: number
): number {
  if (timeDeltaHours <= 0 || scoreDeltas.length === 0) return 0;
  const netDelta = scoreDeltas.reduce((a, b) => a + b, 0);
  const velocity = netDelta / timeDeltaHours;
  return Number(velocity.toFixed(2));
}

/**
 * Command terminal parser for tactical commands.
 */
export interface CommandResult {
  action: 'calibrate' | 'diagnose' | 'select' | 'help' | 'reset' | 'unknown';
  target?: string;
  value?: number;
  feedback: string;
}

export function parseTerminalCommand(input: string): CommandResult {
  const clean = input.trim();
  if (!clean) {
    return { action: 'unknown', feedback: 'Empty command stream. Type help for command registry.' };
  }

  const tokens = clean.split(/\s+/);
  const root = tokens[0].toLowerCase();

  switch (root) {
    case 'help':
    case '?':
      return {
        action: 'help',
        feedback: 'TACTICAL COMMANDS: calibrate <val> | diagnose <module_code> | select <module_id> | reset',
      };

    case 'calibrate': {
      const val = parseFloat(tokens[1]);
      if (isNaN(val)) {
        return {
          action: 'calibrate',
          feedback: 'SYNTAX ERROR: calibrate requires a float parameter (e.g., calibrate 1.42)',
        };
      }
      return {
        action: 'calibrate',
        value: val,
        feedback: `CALIBRATION INITIATED: Injecting state value ${val}`,
      };
    }

    case 'diagnose': {
      const mod = tokens[1] || 'ACTIVE';
      return {
        action: 'diagnose',
        target: mod,
        feedback: `DIAGNOSTIC SWEEP ROUTINE EXECUTED FOR [${mod.toUpperCase()}]`,
      };
    }

    case 'select': {
      const targetId = tokens[1];
      if (!targetId) {
        return { action: 'unknown', feedback: 'ERROR: select requires a target index or module code.' };
      }
      return {
        action: 'select',
        target: targetId,
        feedback: `CHANNEL ROUTED TO TARGET [${targetId.toUpperCase()}]`,
      };
    }

    case 'reset':
      return {
        action: 'reset',
        feedback: 'TELEMETRY BASES RE-INITIALIZED TO STANDARD MATRIX',
      };

    default:
      return {
        action: 'unknown',
        feedback: `UNRECOGNIZED DIRECTIVE: "${clean}". Enter "help" for syntax registry.`,
      };
  }
}

/**
 * Step response simulation for a 2nd order cyber-physical control loop (e.g. inverted pendulum or actuator).
 */
export function simulateCyberPhysicalStep(
  kp: number,
  ki: number,
  kd: number,
  steps: number = 40
): Array<{ t: number; y: number; setpoint: number; error: number }> {
  const dt = 0.05;
  const setpoint = 1.0;
  let pos = 0;
  let vel = 0;
  let integral = 0;
  let prevError = setpoint - pos;

  const data: Array<{ t: number; y: number; setpoint: number; error: number }> = [];

  // Initial state at t = 0
  data.push({
    t: 0,
    y: 0,
    setpoint,
    error: Number((setpoint - pos).toFixed(3)),
  });

  for (let i = 1; i <= steps; i++) {
    const t = Number((i * dt).toFixed(2));
    const error = setpoint - pos;
    integral += error * dt;
    const derivative = (error - prevError) / dt;
    prevError = error;

    // Control effort
    const u = kp * error + ki * integral + kd * derivative;

    // Simplified plant dynamics (mass m=1, friction b=0.8)
    const accel = (u - 0.8 * vel) / 1.0;
    vel += accel * dt;
    pos += vel * dt;

    data.push({
      t,
      y: Number(pos.toFixed(3)),
      setpoint,
      error: Number(error.toFixed(3)),
    });
  }

  return data;
}

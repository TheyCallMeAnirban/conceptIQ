import { ModuleTrack, CognitiveVector, TelemetryLog } from '../types/hud';

export const INITIAL_COGNITIVE_VECTORS: CognitiveVector[] = [
  { id: 'vec_cyber', label: 'CYBER-PHYSICAL', value: 92.4, historicalValue: 88.0, velocity: 1.8, decayRate: 0.12, status: 'nominal' },
  { id: 'vec_quantum', label: 'QUANTUM LOGIC', value: 86.8, historicalValue: 84.2, velocity: 2.4, decayRate: 0.18, status: 'nominal' },
  { id: 'vec_neural', label: 'NEURAL ATTRACTOR', value: 74.2, historicalValue: 79.5, velocity: -1.2, decayRate: 0.25, status: 'divergent' },
  { id: 'vec_thermo', label: 'ENTROPY FLUX', value: 83.5, historicalValue: 81.0, velocity: 0.9, decayRate: 0.14, status: 'nominal' },
  { id: 'vec_kalman', label: 'STOCHASTIC FILTER', value: 88.9, historicalValue: 85.1, velocity: 1.5, decayRate: 0.10, status: 'nominal' },
  { id: 'vec_discrete', label: 'GRAPH AUTOMATA', value: 90.6, historicalValue: 89.0, velocity: 0.6, decayRate: 0.08, status: 'nominal' },
];

export const INITIAL_MODULES: ModuleTrack[] = [
  {
    id: 'mod_1',
    code: 'MOD: CYBER_PHYS_01',
    title: 'Closed-Loop PID Feedback Stabilization',
    domain: 'Dynamic Control Systems',
    status: 'active',
    mastery: 92.4,
    retention: 94.1,
    activeConcept: 'Proportional-Integral Damping Stability Margin',
    problemPrompt: {
      title: 'Actuator Phase Margin Calibration',
      description: 'An inverted robotic pendulum experiences boundary limit oscillations due to phase lag in the magnetic actuator coil. The telemetry model requires adjusting the proportional gain $K_p$ to prevent resonant blowout without inducing under-damped chatter.',
      systemEquation: 'u(t) = K_p · e(t) + K_i ∫ e(τ)dτ + K_d · [de(t)/dt]',
      parameterName: 'Proportional Gain (Kp)',
      parameterUnit: 'V/rad',
      currentValue: 1.45,
      targetMin: 0.2,
      targetMax: 3.5,
      nominalTarget: 1.45,
      tolerance: 0.08,
      contextExplanation: 'Critical damping boundary is localized at Kp = 1.45. Operating above 1.53 triggers high-frequency chatter; below 1.37 causes sluggish state recovery.',
      socraticHints: [
        'Notice that system inertia is m=1.0 kg with damping coefficient b=0.8.',
        'When Kp is set too low (<1.2), position error decays logarithmically rather than settling promptly.',
        'Calibrate Kp to exactly 1.45 to align phase margin with 48.6 degrees.'
      ],
      options: [
        {
          id: 'opt_1',
          label: 'Inject lead-lag compensator to elevate phase margin by 12°',
          isNominal: true,
          explanation: 'Optimal: Lead compensator advances phase near crossover frequency, suppressing high-frequency resonant modes.'
        },
        {
          id: 'opt_2',
          label: 'Quadruple integral gain Ki to eliminate steady-state offset rapidly',
          isNominal: false,
          explanation: 'Suboptimal: Elevating Ki introduces phase lag at low frequencies, creating low-frequency hunting oscillation.'
        },
        {
          id: 'opt_3',
          label: 'De-energize derivative gain Kd entirely to remove sensor noise amplification',
          isNominal: false,
          explanation: 'Divergent: Eliminating Kd drops the system damping ratio to critically low levels, risking overshoot.'
        }
      ]
    }
  },
  {
    id: 'mod_2',
    code: 'MOD: QUANTUM_LOGIC_02',
    title: 'State Vector Superposition & Phase Rotation',
    domain: 'Quantum Computational Physics',
    status: 'nominal',
    mastery: 86.8,
    retention: 91.0,
    activeConcept: 'Bloch Sphere Polar Phase Coherence',
    problemPrompt: {
      title: 'Hadamard Projection & Phase Alignment',
      description: 'A superconducting transmon qubit is initialized in state |0⟩. A microwave pulse sequences rotation along the Y-axis. Align the polar angle θ to achieve an equal superposition state.',
      systemEquation: '|ψ⟩ = cos(θ / 2)|0⟩ + e^{iφ} · sin(θ / 2)|1⟩',
      parameterName: 'Polar Angle (θ)',
      parameterUnit: 'rad',
      currentValue: 0.785,
      targetMin: 0.0,
      targetMax: 3.1415,
      nominalTarget: 1.5708, // pi/2
      tolerance: 0.05,
      contextExplanation: 'Equal superposition (|0⟩ + |1⟩)/√2 requires θ = π/2 ≈ 1.5708 radians, placing the state vector on the Bloch sphere equator.',
      socraticHints: [
        'Recall that cos(π/4) = 1/√2 and sin(π/4) = 1/√2.',
        'Since the amplitude coefficients are cos(θ/2) and sin(θ/2), θ/2 must equal π/4.',
        'Thus polar phase θ should be set to 1.57 rad.'
      ],
      options: [
        {
          id: 'q_opt_1',
          label: 'Apply microwave π/2 rotation about the Y-axis',
          isNominal: true,
          explanation: 'Nominal: Prepares equal amplitude state (|0⟩ + |1⟩)/√2 with zero relative phase.'
        },
        {
          id: 'q_opt_2',
          label: 'Apply Pauli-X gate to invert state directly into |1⟩',
          isNominal: false,
          explanation: 'Incorrect: A Pauli-X gate flips |0⟩ to |1⟩, producing a pure computational basis state rather than a superposition.'
        }
      ]
    }
  },
  {
    id: 'mod_3',
    code: 'MOD: NEURAL_ATTRACTOR_03',
    title: 'Recurrent Attractor Energy Basin Depth',
    domain: 'Cognitive Cybernetics',
    status: 'review_required',
    mastery: 74.2,
    retention: 78.5,
    activeConcept: 'Lyapunov Energy Descent & Spurious Minima',
    problemPrompt: {
      title: 'Attractor Temperature Annealing',
      description: 'The recurrent associative memory matrix is trapped in a shallow spurious local minimum. Tune the annealing stochastic noise parameter T to allow escape without destroying stored memories.',
      systemEquation: 'E = -0.5 · ∑∑ w_{ij} s_i s_j + ∑ θ_i s_i',
      parameterName: 'Thermal Noise (T)',
      parameterUnit: 'kBT',
      currentValue: 0.85,
      targetMin: 0.05,
      targetMax: 1.5,
      nominalTarget: 0.35,
      tolerance: 0.04,
      contextExplanation: 'T = 0.35 provides sufficient stochastic thermal excitation to hop barrier ΔE=0.22 while preserving the fundamental memory basin depth.',
      socraticHints: [
        'Higher temperature (T > 0.6) flattens the energy landscape, causing pattern amnesia.',
        'Zero temperature (T = 0) freezes the network in false metastable states.',
        'The optimal transition threshold is T = 0.35.'
      ]
    }
  },
  {
    id: 'mod_4',
    code: 'MOD: NON_EQUIL_THERMO_04',
    title: 'Non-Equilibrium Entropy Production Flux',
    domain: 'Statistical Cybernetics',
    status: 'nominal',
    mastery: 83.5,
    retention: 87.2,
    activeConcept: 'Onsager Reciprocal Transport Coupling',
    problemPrompt: {
      title: 'Phenomenological Cross-Flux Tuning',
      description: 'Coupled thermal and thermoelectric currents across a nanostructured thermoelectric interface must satisfy Onsager reciprocity L12 = L21 while maximizing power transfer efficiency.',
      systemEquation: 'J_i = ∑ L_{ik} · X_k ;  L_{12} = L_{21}',
      parameterName: 'Cross-Coupling Coefficient (L12)',
      parameterUnit: 'A·m/K',
      currentValue: 2.10,
      targetMin: 0.5,
      targetMax: 4.0,
      nominalTarget: 2.10,
      tolerance: 0.1,
      contextExplanation: 'L12 = 2.10 matches the Peltier heat absorption rate with the Seebeck voltage gradient.',
      socraticHints: [
        'Onsager reciprocal symmetry guarantees microscopic time-reversibility.',
        'Coupling ratio must preserve positive definite entropy production σ > 0.'
      ]
    }
  }
];

export const INITIAL_LOGS: TelemetryLog[] = [
  { id: 'log_1', timestamp: '06:21:04', line: 104, channel: '// MOD: CYBER_PHYS_01', type: 'nominal', message: 'Phase margin calibrated to 48.6 deg. System stability nominal.' },
  { id: 'log_2', timestamp: '06:21:12', line: 105, channel: '// SYS: COGNITIVE_HUB', type: 'nominal', message: 'Mastery velocity tracking at +2.18% / cycle.' },
  { id: 'log_3', timestamp: '06:21:28', line: 106, channel: '// MOD: NEURAL_ATTRACTOR_03', type: 'warning', message: 'Spurious attractor basin detected at node N-14. Review recommended.' },
  { id: 'log_4', timestamp: '06:21:40', line: 107, channel: '// RADIAL: ORBIT_CORE', type: 'nominal', message: 'Comprehension bandwidth locked at 84.6% optimal bandwidth.' },
  { id: 'log_5', timestamp: '06:21:55', line: 108, channel: '// SYS: RETENTION_RADAR', type: 'info', message: 'Ebbinghaus decay index normalized against 24h stability model.' },
];

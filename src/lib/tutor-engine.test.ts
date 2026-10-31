import test from 'node:test';
import assert from 'node:assert/strict';
import {
  calculateSpiderRadarVertices,
  evaluateStateVectorResponse,
  calculateComprehensionBandwidth,
  calculateRetentionDecay,
  calculateMasteryVelocity,
  parseTerminalCommand,
  simulateCyberPhysicalStep,
} from './tutor-engine';

test('Spider Radar calculation returns symmetric circular coordinates', () => {
  const vectors = [
    { id: 'v1', label: 'Quantum', value: 100 },
    { id: 'v2', label: 'Control', value: 50 },
    { id: 'v3', label: 'Neural', value: 0 },
    { id: 'v4', label: 'Thermo', value: 100 },
  ];
  const center = { x: 100, y: 100 };
  const radius = 80;

  const vertices = calculateSpiderRadarVertices(vectors, radius, center);
  assert.equal(vertices.length, 4);

  // First vertex (angle -PI/2) should be straight up at x=100, y=100 - 80 = 20
  assert.equal(vertices[0].x, 100);
  assert.equal(vertices[0].y, 20);

  // Third vertex at value 0 should be right at center
  assert.equal(vertices[2].x, 100);
  assert.equal(vertices[2].y, 100);
});

test('State Vector evaluation yields nominal status within tolerance', () => {
  const result = evaluateStateVectorResponse(1.42, 1.40, 0.05);
  assert.equal(result.isNominal, true);
  assert.equal(result.deviation, 0.02);
  assert.ok(result.score > 85);
  assert.equal(result.statusMsg, 'NOMINAL SYSTEM COUPLING');
});

test('State Vector evaluation identifies divergent system breach outside tolerance', () => {
  const result = evaluateStateVectorResponse(2.1, 1.40, 0.05);
  assert.equal(result.isNominal, false);
  assert.ok(result.deviation > 0.5);
  assert.ok(result.score < 50);
  assert.match(result.statusMsg, /OVER-SATURATED DIVERGENCE/);
});

test('Comprehension bandwidth respects target latency bounds', () => {
  const fastAccurate = calculateComprehensionBandwidth(0.95, 1200);
  const slowInaccurate = calculateComprehensionBandwidth(0.4, 6000);

  assert.ok(fastAccurate > 85);
  assert.ok(slowInaccurate < 60);
});

test('Retention decay follows negative exponential curve', () => {
  const fresh = calculateRetentionDecay(90, 0, 24);
  const aged = calculateRetentionDecay(90, 48, 24);

  assert.equal(fresh, 90);
  assert.ok(aged < 60);
  assert.ok(aged > 30);
});

test('Mastery velocity handles positive score deltas over time', () => {
  const velocity = calculateMasteryVelocity([5, 8, 3], 2);
  assert.equal(velocity, 8.0);
});

test('Terminal command parser parses valid tactical commands and rejects errors', () => {
  const cmd1 = parseTerminalCommand('calibrate 2.75');
  assert.equal(cmd1.action, 'calibrate');
  assert.equal(cmd1.value, 2.75);

  const cmd2 = parseTerminalCommand('diagnose MOD_QUANTUM');
  assert.equal(cmd2.action, 'diagnose');
  assert.equal(cmd2.target, 'MOD_QUANTUM');

  const cmd3 = parseTerminalCommand('invalid_directive');
  assert.equal(cmd3.action, 'unknown');
});

test('Cyber-Physical step simulation generates valid time series', () => {
  const steps = simulateCyberPhysicalStep(2.5, 0.5, 1.0, 20);
  assert.equal(steps.length, 21);
  assert.equal(steps[0].t, 0);
  assert.equal(steps[0].y, 0);
  assert.equal(steps[0].setpoint, 1.0);
  // Settling should approach setpoint
  assert.ok(steps[steps.length - 1].y > 0.5);
});

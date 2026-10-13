import { describe, it, expect } from 'vitest';
import {
  formatCurrency,
  formatPercent,
  formatTolerance,
  formatDuration,
  formatPpm,
} from '../lib/formatters';

describe('Formatters', () => {
  it('formats currency correctly without fractional cents', () => {
    expect(formatCurrency(128400)).toBe('$128,400');
    expect(formatCurrency(0)).toBe('$0');
    expect(formatCurrency(5400)).toBe('$5,400');
  });

  it('formats percentages with specified decimals', () => {
    expect(formatPercent(12.4)).toBe('12.4%');
    expect(formatPercent(12.456, 2)).toBe('12.46%');
    expect(formatPercent(85, 0)).toBe('85%');
  });

  it('formats tolerances with signs and units', () => {
    expect(formatTolerance(0.042, 'mm')).toBe('+0.042 mm');
    expect(formatTolerance(-0.015, 'mm')).toBe('-0.015 mm');
  });

  it('formats durations in mm:ss', () => {
    expect(formatDuration(248)).toBe('4m 08s');
    expect(formatDuration(65)).toBe('1m 05s');
    expect(formatDuration(0)).toBe('0m 00s');
  });

  it('formats PPM values with commas', () => {
    expect(formatPpm(12500)).toBe('12,500 ppm');
    expect(formatPpm(450)).toBe('450 ppm');
  });
});

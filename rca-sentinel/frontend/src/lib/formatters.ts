/**
 * Financial & Operational Formatting Utilities
 * Adheres to tabular numeral standards and clear unit specifications.
 */

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatPercent(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function formatTolerance(value: number, unit: string = 'mm'): string {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(3)} ${unit}`;
}

export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs < 10 ? '0' : ''}${secs}s`;
}

export function formatPpm(ppm: number): string {
  return `${ppm.toLocaleString()} ppm`;
}

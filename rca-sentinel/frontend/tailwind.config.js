/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "var(--surface-canvas)",
        panel: "var(--surface-panel)",
        raised: "var(--surface-raised)",
        overlay: "var(--surface-overlay)",
        muted: "var(--surface-muted)",
        
        subtle: "var(--border-subtle)",
        strong: "var(--border-strong)",
        active: "var(--border-active)",

        primary: "var(--text-primary)",
        secondary: "var(--text-secondary)",
        dim: "var(--text-muted)",
        inverse: "var(--text-inverse)",

        healthy: {
          DEFAULT: "var(--status-healthy)",
          bg: "var(--status-healthy-bg)",
          border: "var(--status-healthy-border)",
        },
        caution: {
          DEFAULT: "var(--status-caution)",
          bg: "var(--status-caution-bg)",
          border: "var(--status-caution-border)",
        },
        critical: {
          DEFAULT: "var(--status-critical)",
          bg: "var(--status-critical-bg)",
          border: "var(--status-critical-border)",
        },
        cobalt: {
          DEFAULT: "var(--agent-cobalt)",
          bg: "var(--agent-cobalt-bg)",
          border: "var(--agent-cobalt-border)",
        },
      },
      fontFamily: {
        heading: ['"Barlow Semi Condensed"', 'sans-serif'],
        body: ['"Public Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        xs: "2px",
        sm: "3px",
        DEFAULT: "4px",
        md: "6px",
        lg: "8px",
      },
    },
  },
  plugins: [],
}

import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          0: "var(--surface-0)",
          1: "var(--surface-1)",
          2: "var(--surface-2)",
          3: "var(--surface-3)",
          4: "var(--surface-4)"
        },
        border: {
          DEFAULT: "var(--border)",
          bright: "var(--border-bright)",
          focus: "var(--border-focus)",
          divider: "var(--divider)"
        },
        text: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          tertiary: "var(--text-tertiary)"
        },
        accent: {
          DEFAULT: "var(--accent)",
          hover: "var(--accent-hover)",
          fg: "var(--accent-fg)"
        },
        "accent-2": {
          DEFAULT: "var(--accent-2)",
          hover: "var(--accent-2-hover)",
          fg: "var(--accent-2-fg)"
        },
        status: {
          blue: "var(--status-blue)",
          green: "var(--status-green)",
          orange: "var(--status-orange)",
          red: "var(--status-red)",
          purple: "var(--status-purple)",
          gold: "var(--status-gold)",
          violet: "var(--status-violet)",
          rose: "var(--status-rose)",
          cyan: "var(--status-cyan)",
          lime: "var(--status-lime)"
        }
      },
      borderRadius: {
        sm: "4px",
        md: "6px",
        lg: "8px",
        xl: "12px"
      }
    }
  },
  plugins: []
} satisfies Config;

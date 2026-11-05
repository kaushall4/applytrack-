import type { Config } from "tailwindcss";

/**
 * Design system. Colors are driven by CSS variables (see index.css) so light
 * and dark themes share one set of semantic tokens. Status colors encode
 * meaning in jewel tones: stone=applied, sapphire=interview, emerald=offer,
 * garnet=rejection, ochre=ghosted.
 */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--bg) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        "surface-2": "rgb(var(--surface-2) / <alpha-value>)",
        border: "rgb(var(--border) / <alpha-value>)",
        fg: "rgb(var(--fg) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        brand: {
          DEFAULT: "rgb(var(--brand) / <alpha-value>)",
          fg: "rgb(var(--brand-fg) / <alpha-value>)",
        },
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', "Georgia", '"Times New Roman"', "serif"],
        sans: [
          '"Inter Variable"',
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.125rem",
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(var(--shadow-tint) / 0.04), 0 12px 28px -18px rgb(var(--shadow-tint) / 0.22)",
        lift: "0 1px 2px 0 rgb(var(--shadow-tint) / 0.05), 0 20px 36px -20px rgb(var(--shadow-tint) / 0.32)",
        pop: "0 24px 60px -24px rgb(var(--shadow-tint) / 0.45)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out",
      },
    },
  },
  plugins: [],
} satisfies Config;

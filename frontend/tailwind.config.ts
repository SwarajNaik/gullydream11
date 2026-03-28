import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dream11 color palette
        dream: {
          bg: {
            primary: "#1A1A2E",    // Main background
            secondary: "#16213E",  // Slightly lighter
            card: "#0F3460",       // Card background
            elevated: "#1B2845",   // Elevated surfaces
          },
          accent: {
            red: "#E94560",        // Dream11 signature red
            "red-hover": "#D13550",
            "red-dim": "rgba(233, 69, 96, 0.15)",
          },
          success: "#00C853",
          "success-dim": "rgba(0, 200, 83, 0.15)",
          warning: "#FFD600",
          "warning-dim": "rgba(255, 214, 0, 0.15)",
          info: "#2196F3",
          "info-dim": "rgba(33, 150, 243, 0.15)",
          text: {
            primary: "#FFFFFF",
            secondary: "#9E9E9E",
            muted: "#666666",
          },
          border: {
            DEFAULT: "#2A2A4A",
            strong: "#3A3A5A",
            subtle: "#1F1F3A",
          },
          // Player role colors
          role: {
            wk: "#FF6B6B",
            bat: "#4ECDC4",
            ar: "#45B7D1",
            bowl: "#96CEB4",
          },
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      borderRadius: {
        card: "12px",
        button: "8px",
        pill: "20px",
      },
      spacing: {
        "safe-bottom": "env(safe-area-inset-bottom, 0px)",
        "safe-top": "env(safe-area-inset-top, 0px)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;

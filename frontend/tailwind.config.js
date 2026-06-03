export default {
  content: ["./index.html", "./src/**/*.{vue,ts,js}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0d1b2a",
        surface: "#132438",
        "surface-2": "#1a314a",
        primary: "#0052ff",
        gain: "#05b169",
        loss: "#cf202f",
        "text-primary": "#f0f4f8",
        "text-secondary": "#8899aa",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: { pill: "100px" },
    },
  },
};

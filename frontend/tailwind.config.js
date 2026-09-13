module.exports = {
  content: ["./src/**/*.{js,jsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        bg: "#FFFFFF",
        surface: "#F8F9FA",
        "surface-hover": "#E9ECEF",
        primary: "#002FA7",
        "primary-hover": "#00227A",
        ink: "#111111",
        muted: "#6C757D",
        success: "#198754",
        danger: "#DC3545",
        warn: "#FFC107",
        line: "#DEE2E6",
      },
      fontFamily: {
        heading: ["Cabinet Grotesk", "IBM Plex Sans", "sans-serif"],
        body: ["IBM Plex Sans", "system-ui", "sans-serif"],
      },
      borderRadius: {
        sm: "4px",
      },
      keyframes: {
        pulsering: {
          "0%": { transform: "scale(0.95)", opacity: "0.7" },
          "70%": { transform: "scale(1.6)", opacity: "0" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
      },
      animation: {
        pulsering: "pulsering 1.6s ease-out infinite",
      },
    },
  },
  plugins: [],
};

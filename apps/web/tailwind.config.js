/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/features/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        warm: {
          50:  "#fdf8f3",
          100: "#f7ede0",
          200: "#eed9bf",
          300: "#e2c092",
          400: "#d4a566",
          500: "#c58a44",
          600: "#b07136",
          700: "#8e582b",
          800: "#6f4522",
          900: "#57371d",
        },
      },
    }
  },
  plugins: []
};

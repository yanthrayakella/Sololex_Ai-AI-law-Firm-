/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        ink: { 950: "#0b1220", 900: "#111827", 600: "#4b5563" },
        mint: { 500: "#10b981", 600: "#059669" },
        sky: { 500: "#0ea5e9" },
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f4ff",
          400: "#6b84f8",
          500: "#4f6ef7",
          600: "#3a56e8",
          700: "#2a43c9",
          900: "#1a2a8a",
        },
      },
    },
  },
  plugins: [],
}

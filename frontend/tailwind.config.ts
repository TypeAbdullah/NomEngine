import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        nom: {
          50: "#f0f7ff",
          100: "#e0effe",
          200: "#bae0fd",
          300: "#7cc7fc",
          400: "#36abf8",
          500: "#0c8ee9",
          600: "#0170c7",
          700: "#0259a1",
          800: "#064c84",
          900: "#0b3f6e",
          950: "#072849",
        },
        dark: {
          bg: "#202124",
          surface: "#303134",
          border: "#3c4043",
          text: "#e8eaed",
          muted: "#9aa0a6",
          link: "#8ab4f8",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;

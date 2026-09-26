/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        ink: "#1f2933",
        muted: "#5f6c7b",
        line: "#d9dee5",
        paper: "#f7f8fa",
        brand: "#1d5c8f",
        provisional: "#b45309",
        final: "#15803d",
        danger: "#b91c1c",
      },
    },
  },
  plugins: [],
};

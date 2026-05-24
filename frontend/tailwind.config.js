/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'naija-green': '#008751',
        'naija-white': '#FFFFFF',
      },
    },
  },
  plugins: [],
}

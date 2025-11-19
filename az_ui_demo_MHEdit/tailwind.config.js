/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#A82626',
        'secondary': '#109B9D',
        'gray': {
          '50': '#F2F2F2',
          '100': '#EAEAEA',
          '200': '#D5D5D5',
          '300': '#C0C0C0',
          '400': '#A9A9A9',
          '500': '#7F7F7F',
        },
      },
    },
  },
  plugins: [],
}


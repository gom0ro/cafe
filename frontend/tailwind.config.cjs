module.exports = {
  content: ['./index.html', './src/**/*.{vue,ts,js}'],
  theme: {
    extend: {
      borderRadius: {
        'lg': '20px',
        'xl': '28px'
      },
      colors: {
        accent: '#3b82f6',
        morning: '#bde0ff',
        evening: '#ff7a59',
        night: '#0b1020'
      }
    }
  },
  plugins: []
}

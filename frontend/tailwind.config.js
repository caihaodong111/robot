/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  corePlugins: {
    preflight: false
  },
  theme: {
    extend: {
      colors: {
        benz: {
          black: '#000000',
          dark: '#0B0B0C',
          'dark-gray': '#1D1D1F',
          gray: '#86868B',
          light: '#F5F5F7',
          blue: '#0071E3',
          cyan: '#00FFFF'
        }
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.75rem'
      },
      fontFamily: {
        sans: ['"SF Pro Display"', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif']
      },
      transitionTimingFunction: {
        'apple-ease': 'cubic-bezier(0.28, 0.11, 0.32, 1)'
      },
      boxShadow: {
        'glow-blue': '0 0 20px 2px rgba(0, 113, 227, 0.5)',
        'glow-cyan': '0 0 15px 1px rgba(0, 255, 255, 0.4)',
        panel:
          '0 30px 120px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.08)'
      },
      backgroundImage: {
        'portal-grid':
          'linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)'
      }
    }
  },
  plugins: []
}

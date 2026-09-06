/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0B0F19',
          850: '#111827',
          800: '#1F2937',
          700: '#374151',
          600: '#4B5563'
        },
        brand: {
          blue: '#3B82F6',
          cyan: '#06B6D4',
          emerald: '#10B981',
          amber: '#F59E0B',
          rose: '#F43F5E',
          purple: '#8B5CF6'
        }
      },
      animation: {
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'flash-red': 'flashRed 1.5s ease-in-out infinite',
      },
      keyframes: {
        flashRed: {
          '0%, 100%': { backgroundColor: 'rgba(239, 68, 68, 0.15)' },
          '50%': { backgroundColor: 'rgba(239, 68, 68, 0.4)' },
        }
      }
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
        },
        status: {
          pending: '#EF4444',
          'pending-bg': '#FEF2F2',
          progress: '#F59E0B',
          'progress-bg': '#FFFBEB',
          done: '#10B981',
          'done-bg': '#F0FDF4',
        },
        neutral: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          300: '#D1D5DB',
          600: '#4B5563',
          900: '#111827',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 15px 35px rgba(15, 23, 42, 0.08)',
      },
    },
  },
  plugins: [],
}


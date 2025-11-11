/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Fortress theme - Secure, organized, modern
        fortress: {
          // Dark backgrounds
          950: '#0a0e14',
          900: '#0f1419',
          850: '#141921',
          800: '#1a1f29',
          
          // Neutral tones
          700: '#2d3748',
          600: '#4a5568',
          500: '#718096',
          400: '#a0aec0',
          300: '#cbd5e0',
          200: '#e2e8f0',
          100: '#f7fafc',
        },
        
        // Accent colors
        secure: {
          // Blue accents for secure actions
          DEFAULT: '#3b82f6',
          light: '#60a5fa',
          dark: '#2563eb',
        },
        
        success: {
          // Green for success states
          DEFAULT: '#10b981',
          light: '#34d399',
          dark: '#059669',
        },
        
        alert: {
          // Red for restricted/alert
          DEFAULT: '#ef4444',
          light: '#f87171',
          dark: '#dc2626',
        },
        
        warning: {
          // Yellow for warnings
          DEFAULT: '#f59e0b',
          light: '#fbbf24',
          dark: '#d97706',
        },
        
        // Access level colors
        public: '#10b981',      // Green
        internal: '#f59e0b',    // Yellow
        confidential: '#ef4444', // Red
        restricted: '#7c3aed',   // Purple
      },
      
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      
      boxShadow: {
        'glow-sm': '0 0 10px rgba(59, 130, 246, 0.5)',
        'glow': '0 0 20px rgba(59, 130, 246, 0.6)',
        'glow-lg': '0 0 30px rgba(59, 130, 246, 0.7)',
      },
      
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

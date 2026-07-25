import type { Config } from 'tailwindcss';

/**
 * Design tokens — estética artesanal de Chiloé (paleta piedra / tierra / ágata).
 *
 * Los colores se exponen como variables CSS en `app/globals.css` para que cada
 * fork (ROADMAP Fase 8) pueda re-tematizar cambiando solo esas variables, sin
 * tocar componentes. Los escalares numéricos viven aquí.
 */
const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Neutros cálidos: la "piedra" base de toda la UI.
        piedra: {
          50: 'rgb(var(--color-piedra-50) / <alpha-value>)',
          100: 'rgb(var(--color-piedra-100) / <alpha-value>)',
          200: 'rgb(var(--color-piedra-200) / <alpha-value>)',
          300: 'rgb(var(--color-piedra-300) / <alpha-value>)',
          400: 'rgb(var(--color-piedra-400) / <alpha-value>)',
          500: 'rgb(var(--color-piedra-500) / <alpha-value>)',
          600: 'rgb(var(--color-piedra-600) / <alpha-value>)',
          700: 'rgb(var(--color-piedra-700) / <alpha-value>)',
          800: 'rgb(var(--color-piedra-800) / <alpha-value>)',
          900: 'rgb(var(--color-piedra-900) / <alpha-value>)',
        },
        // Terracota / arcilla: color primario de marca.
        tierra: {
          50: 'rgb(var(--color-tierra-50) / <alpha-value>)',
          100: 'rgb(var(--color-tierra-100) / <alpha-value>)',
          200: 'rgb(var(--color-tierra-200) / <alpha-value>)',
          300: 'rgb(var(--color-tierra-300) / <alpha-value>)',
          400: 'rgb(var(--color-tierra-400) / <alpha-value>)',
          500: 'rgb(var(--color-tierra-500) / <alpha-value>)',
          600: 'rgb(var(--color-tierra-600) / <alpha-value>)',
          700: 'rgb(var(--color-tierra-700) / <alpha-value>)',
          800: 'rgb(var(--color-tierra-800) / <alpha-value>)',
          900: 'rgb(var(--color-tierra-900) / <alpha-value>)',
        },
        // Ámbar/miel translúcido de las ágatas: color de acento.
        agata: {
          50: 'rgb(var(--color-agata-50) / <alpha-value>)',
          100: 'rgb(var(--color-agata-100) / <alpha-value>)',
          200: 'rgb(var(--color-agata-200) / <alpha-value>)',
          300: 'rgb(var(--color-agata-300) / <alpha-value>)',
          400: 'rgb(var(--color-agata-400) / <alpha-value>)',
          500: 'rgb(var(--color-agata-500) / <alpha-value>)',
          600: 'rgb(var(--color-agata-600) / <alpha-value>)',
          700: 'rgb(var(--color-agata-700) / <alpha-value>)',
          800: 'rgb(var(--color-agata-800) / <alpha-value>)',
          900: 'rgb(var(--color-agata-900) / <alpha-value>)',
        },
      },
      fontFamily: {
        // Serif editorial para títulos + display; sans para texto; manuscrita de acento.
        serif: ['var(--font-serif)', 'Georgia', 'serif'],
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        manuscrita: ['var(--font-manuscrita)', 'cursive'],
      },
      maxWidth: {
        prosa: '68ch',
      },
    },
  },
  plugins: [],
};

export default config;

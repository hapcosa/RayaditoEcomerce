/**
 * Paleta de la app admin. Espeja los tokens de `web/app/globals.css`
 * (piedra / tierra / agata) para que el sitio y la app se vean de la misma
 * marca. Al re-tematizar un fork se cambia `Brand` y nada mas.
 */

import '@/global.css';

import { Platform } from 'react-native';

/** Tokens de marca, en hex. Equivalen a las variables RGB de la web. */
export const Brand = {
  piedra50: '#FAF9F6',
  piedra100: '#F4F1EC',
  piedra200: '#E7E2D9',
  piedra400: '#B5AB9B',
  piedra700: '#5C554B',
  piedra800: '#3F3A33',
  piedra900: '#26231F',
  tierra50: '#FAF3EE',
  tierra500: '#AD5C3A',
  tierra600: '#944A2D',
  agata500: '#CB872F',
  /** Oxido: destructivo/rechazado. Ya lo usa `utils/order-status.ts`. */
  oxido: '#A15C4A',
  /** Negro y naranjo tomados del PNG del logo: son los colores de la marca. */
  logoNegro: '#1D1D1B',
  logoNaranjo: '#DA5F15',
  /** Grises entre el negro del logo y la piedra, para superficies oscuras. */
  carbon800: '#2A2A28',
  carbon700: '#3A3A37',
  carbon400: '#9A9892',
} as const;

export const Colors = {
  light: {
    text: Brand.piedra900,
    background: Brand.piedra50,
    backgroundElement: Brand.piedra100,
    backgroundSelected: Brand.piedra200,
    textSecondary: Brand.piedra700,
    /** Primario de marca: chip elegido, boton de accion, FAB. */
    accent: Brand.tierra500,
    /** Texto/icono que va encima de `accent`. */
    onAccent: Brand.piedra50,
    /** Destructivo: eliminar, rechazar, mensajes de error. */
    danger: Brand.oxido,
  },
  dark: {
    text: Brand.piedra50,
    background: Brand.logoNegro,
    backgroundElement: Brand.carbon800,
    backgroundSelected: Brand.carbon700,
    textSecondary: Brand.carbon400,
    /** El naranjo del logo: sobre el negro rinde mucho mejor que el tierra. */
    accent: Brand.logoNaranjo,
    onAccent: Brand.piedra50,
    danger: Brand.oxido,
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Fonts = Platform.select({
  ios: {
    /** iOS `UIFontDescriptorSystemDesignDefault` */
    sans: 'system-ui',
    /** iOS `UIFontDescriptorSystemDesignSerif` */
    serif: 'ui-serif',
    /** iOS `UIFontDescriptorSystemDesignRounded` */
    rounded: 'ui-rounded',
    /** iOS `UIFontDescriptorSystemDesignMonospaced` */
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: 'var(--font-display)',
    serif: 'var(--font-serif)',
    rounded: 'var(--font-rounded)',
    mono: 'var(--font-mono)',
  },
});

export const Spacing = {
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
} as const;

export const BottomTabInset = Platform.select({ ios: 50, android: 80 }) ?? 0;
export const MaxContentWidth = 800;

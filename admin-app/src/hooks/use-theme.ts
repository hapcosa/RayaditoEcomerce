/**
 * La app va siempre en el esquema oscuro (fondo negro del logo). Es lo que el
 * dueno prefiere para trabajar desde el taller, y el sitio va aparte en claro.
 * `Colors.light` sigue definido por si mas adelante se ofrece la opcion.
 */

import { Colors } from '@/constants/theme';

export function useTheme() {
  return Colors.dark;
}

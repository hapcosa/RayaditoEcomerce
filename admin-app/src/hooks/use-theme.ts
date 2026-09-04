/**
 * La app va siempre en el esquema claro de la marca (fondo piedra), igual que
 * el sitio: en oscuro el fondo se iba a casi negro y desentonaba con la web.
 * `Colors.dark` sigue definido por si mas adelante se ofrece la opcion.
 */

import { Colors } from '@/constants/theme';

export function useTheme() {
  return Colors.light;
}

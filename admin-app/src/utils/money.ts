/**
 * Formato de dinero en CLP (entero, sin decimales). Ver AGENTS.md.
 * No dependemos de Intl (Hermes lo trae recortado); formateo manual con
 * separador de miles chileno (punto).
 */
export function formatCLP(value: number): string {
  const n = Math.round(value);
  const sign = n < 0 ? '-' : '';
  const digits = Math.abs(n).toString();
  const withDots = digits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `${sign}$${withDots}`;
}

/** Formatea un entero CLP con separadores de miles: 12500 → "$ 12.500" */
export function formatCLP(amount: number): string {
  return `$ ${amount.toLocaleString('es-CL')}`;
}

import type { Address, AddressFields } from '@/types/checkout';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api';

function authHeaders(access: string) {
  return { 'Content-Type': 'application/json', Authorization: `JWT ${access}` };
}

/** Junta los errores de DRF (`{campo: [mensaje]}`) en una sola línea. */
async function fallar(res: Response, porDefecto: string): Promise<never> {
  const err = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  const msg = (Object.values(err).flat() as string[]).filter(Boolean).join(' ');
  throw new Error(msg || porDefecto);
}

/**
 * Direcciones guardadas del usuario. Devuelve `[]` si la sesión no sirve para
 * que el checkout siga funcionando con una dirección escrita a mano.
 */
export async function fetchAddresses(access: string): Promise<Address[]> {
  const res = await fetch(`${API}/profile/addresses/`, {
    headers: authHeaders(access),
    cache: 'no-store',
  });
  if (!res.ok) return [];
  return (await res.json()) as Address[];
}

export async function createAddress(
  access: string,
  data: Partial<AddressFields>,
): Promise<Address> {
  const res = await fetch(`${API}/profile/addresses/`, {
    method: 'POST',
    headers: authHeaders(access),
    body: JSON.stringify(data),
    cache: 'no-store',
  });
  if (!res.ok) await fallar(res, 'Error al guardar la dirección');
  return (await res.json()) as Address;
}

export async function updateAddress(
  access: string,
  id: number,
  data: Partial<AddressFields>,
): Promise<Address> {
  const res = await fetch(`${API}/profile/addresses/${id}/`, {
    method: 'PATCH',
    headers: authHeaders(access),
    body: JSON.stringify(data),
    cache: 'no-store',
  });
  if (!res.ok) await fallar(res, 'Error al actualizar la dirección');
  return (await res.json()) as Address;
}

export async function deleteAddress(access: string, id: number): Promise<void> {
  const res = await fetch(`${API}/profile/addresses/${id}/`, {
    method: 'DELETE',
    headers: authHeaders(access),
    cache: 'no-store',
  });
  if (!res.ok) await fallar(res, 'Error al borrar la dirección');
}

/** Marca una como preferida; el backend desmarca la anterior. */
export function setDefaultAddress(access: string, id: number): Promise<Address> {
  return updateAddress(access, id, { is_default: true });
}

/** Texto de una línea para mostrarla en listas y resúmenes. */
export function resumirDireccion(a: Address): string {
  return [a.address_line_1, a.city, a.country_region, a.zipcode]
    .map((parte) => parte?.trim())
    .filter(Boolean)
    .join(', ');
}

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api';

export interface Region {
  name: string;
  communes: string[];
}

/**
 * Regiones y comunas de Chile que ya sirve el backend (`shipping.locations`).
 *
 * Devuelve `[]` si la llamada falla: los formularios de dirección caen a texto
 * libre en vez de bloquearse.
 */
export async function fetchRegions(): Promise<Region[]> {
  try {
    const res = await fetch(`${API}/shipp/locations`, { cache: 'force-cache' });
    if (!res.ok) return [];
    const data = (await res.json()) as { regions?: Region[] };
    return data.regions ?? [];
  } catch {
    return [];
  }
}

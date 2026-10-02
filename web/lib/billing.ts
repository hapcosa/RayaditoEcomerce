const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api';

/** Datos para emitir factura. Espeja `billing.InvoiceRequest` del backend. */
export interface InvoiceFields {
  rut: string;
  business_name: string;
  activity: string;
  address: string;
  commune: string;
  email: string;
}

export const INVOICE_VACIA: InvoiceFields = {
  rut: '',
  business_name: '',
  activity: '',
  address: '',
  commune: '',
  email: '',
};

/**
 * ¿El checkout ofrece "Necesito factura"? Falso hasta que la tienda tenga
 * inicio de actividades y lo active en el backend (ver docs/SII.md). Ante
 * cualquier error responde falso: sin esto se puede comprar igual.
 */
export async function fetchInvoicesEnabled(): Promise<boolean> {
  try {
    const res = await fetch(`${API}/billing/config`, { cache: 'no-store' });
    if (!res.ok) return false;
    const data = (await res.json()) as { invoices_enabled?: boolean };
    return data.invoices_enabled === true;
  } catch {
    return false;
  }
}

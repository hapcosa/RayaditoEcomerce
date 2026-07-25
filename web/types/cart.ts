import type { Product } from './product';

/** Item del carrito hidratado desde el backend (endpoint synch). */
export interface HydratedCartItem {
  count: number;
  product: Product;
}

export interface ShippingOption {
  id: number;
  name: string;
  time_to_delivery: string;
  description: string;
  /** Precio en CLP entero. */
  price: number;
}

/**
 * Una dirección de la libreta del usuario (`/api/profile/addresses/`).
 *
 * `country_region` guarda la **región** chilena, no un país: el nombre viene del
 * modelo original del backend y lo usan órdenes ya emitidas.
 */
export interface Address {
  id: number;
  /** Alias para reconocerla en la lista ("Casa", "Taller"). Puede venir vacío. */
  label: string;
  first_name: string;
  last_name: string;
  address_line_1: string;
  city: string;
  zipcode: string;
  phone: string;
  country_region: string;
  is_default: boolean;
}

/** Campos editables: la libreta se escribe sin `id` ni banderas derivadas. */
export type AddressFields = Omit<Address, 'id'>;

/** Campos del formulario para checkout de invitado (y creación de perfil). */
export interface CheckoutForm {
  email: string;
  first_name: string;
  last_name: string;
  address_line_1: string;
  city: string;
  state_province_region: string;
  postal_zip_code: string;
  telephone_number: string;
  shipping_id: string;
}

export interface PaymentPreference {
  id: string;
  init_point: string;
  sandbox_init_point: string;
}

export interface OrderStatus {
  order_id: number;
  order_status: string;
  payment_status: string | null;
  transaction_id: string | null;
}

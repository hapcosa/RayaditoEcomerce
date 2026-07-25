export interface SavedProfile {
  id: number;
  first_name: string;
  last_name: string;
  address_line_1: string;
  city: string;
  zipcode: string;
  phone: string;
  country_region: string;
}

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

/** Tipos que espeja los serializers DRF. Moneda siempre en entero CLP. */

export interface Category {
  id: number;
  name: string;
  parent: number | null;
  ProductType: string;
}

export interface AttributeValue {
  id: number;
  value: string;
  attribute: number;
}

export interface Attribute {
  id: number;
  name: string;
  unit: string;
  kind: 'select' | 'number' | 'text';
  values: AttributeValue[];
}

export interface ProductAttributeValue {
  id: number;
  attribute_value: AttributeValue & { attribute: Attribute };
  attribute_name: string;
  attribute_unit: string;
  kind: string;
  value_display: string;
}

export interface ProductVariant {
  id: number;
  sku: string;
  price_override: number | null;
  stock: number;
  is_active: boolean;
  attributes: AttributeValue[];
}

export interface GalleryImage {
  id: number;
  photo: string;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  product_type: string;
  photo: string;
  description: string;
  /** Precio en CLP (entero). */
  price: number;
  /** Precio tachado/comparación en CLP. 0 = no mostrar. */
  compare_price: number;
  category: number;
  sold: boolean;
  status: 'draft' | 'published' | 'archived';
  is_featured: boolean;
  date_created: string;
  available_stock: number;
  attributes: ProductAttributeValue[];
  variants: ProductVariant[];
  gallery: GalleryImage[];
}

export interface Review {
  id: number;
  user: number;
  user_name: string;
  product: number;
  rating: number;
  comment: string;
  verified_purchase: boolean;
  approved: boolean;
  created_at: string;
}

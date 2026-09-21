/**
 * Capa de datos de atributos contra la API admin (`/api/admin/`).
 * Requiere staff (el header JWT lo agrega apiFetch).
 *
 * Un atributo es una definición reutilizable ("Talla", "Métrica europea",
 * "Alto"). `kind` decide cómo se carga el valor en el producto: solo `select`
 * tiene una enumeración propia (`values`); los demás los escribe el staff
 * producto por producto. Ver product/admin_attributes_api.py.
 *
 * OJO con las barras finales: las acciones del router DRF las exigen; sin
 * ellas Django responde 301 y el fetch pierde el método.
 */
import { apiJson } from './client';

/** Cómo se carga el valor del atributo. Espeja `AttributeKind` del backend. */
export type AttributeKind = 'select' | 'text' | 'integer' | 'decimal';

export const KIND_LABEL: Record<AttributeKind, string> = {
  select: 'Selección',
  text: 'Texto',
  integer: 'Entero',
  decimal: 'Decimal',
};

export type AttributeValue = {
  id: number;
  value: string;
  /** Para ordenar/filtrar por número (talla 16 < 17). `null` si no aplica. */
  numeric_value: string | null;
  sort_order: number;
};

export type Attribute = {
  id: number;
  name: string;
  slug: string;
  unit: string;
  kind: AttributeKind;
  /** Genera variantes comprables con stock propio. Solo en `select`. */
  is_variant_option: boolean;
  sort_order: number;
  /** Enumeración; siempre vacía si `kind` no es `select`. */
  values: AttributeValue[];
  /** Productos/variantes que lo usan. Si no es 0, el backend no deja borrarlo. */
  usage_count: number;
};

/** Campos editables de un atributo (el `slug` lo deriva el backend del nombre). */
export type AttributeFields = {
  name: string;
  unit: string;
  kind: AttributeKind;
  is_variant_option: boolean;
  sort_order: number;
};

/** Campos editables de un valor de la enumeración. */
export type AttributeValueFields = {
  value: string;
  numeric_value: string | null;
  sort_order: number;
};

/**
 * Enganche categoría↔atributo. `inherited_from` es `null` si el enganche es de
 * esta categoría, o la ancestra que lo definió: esos no se editan acá.
 */
export type CategoryAttribute = {
  id: number;
  attribute: Attribute;
  is_required: boolean;
  sort_order: number;
  inherited_from: { id: number; name: string } | null;
};

function jsonBody(payload: unknown): RequestInit {
  return {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  };
}

export async function listAttributes(): Promise<Attribute[]> {
  return apiJson<Attribute[]>('/api/admin/attributes/');
}

export async function createAttribute(fields: AttributeFields): Promise<Attribute> {
  return apiJson<Attribute>('/api/admin/attributes/', {
    method: 'POST',
    ...jsonBody(fields),
  });
}

export async function updateAttribute(
  id: number,
  fields: Partial<AttributeFields>,
): Promise<Attribute> {
  return apiJson<Attribute>(`/api/admin/attributes/${id}/`, {
    method: 'PATCH',
    ...jsonBody(fields),
  });
}

/** 409 si hay productos o variantes usándolo (el backend nunca cascadea). */
export async function deleteAttribute(id: number): Promise<void> {
  await apiJson<null>(`/api/admin/attributes/${id}/`, { method: 'DELETE' });
}

/** 400 si el atributo no es `select`: una medida libre no tiene lista fija. */
export async function addAttributeValue(
  attributeId: number,
  fields: AttributeValueFields,
): Promise<AttributeValue> {
  return apiJson<AttributeValue>(`/api/admin/attributes/${attributeId}/values/`, {
    method: 'POST',
    ...jsonBody(fields),
  });
}

export async function updateAttributeValue(
  attributeId: number,
  valueId: number,
  fields: Partial<AttributeValueFields>,
): Promise<AttributeValue> {
  return apiJson<AttributeValue>(
    `/api/admin/attributes/${attributeId}/values/${valueId}/`,
    { method: 'PATCH', ...jsonBody(fields) },
  );
}

/** 409 si algún producto o variante tiene este valor. */
export async function deleteAttributeValue(
  attributeId: number,
  valueId: number,
): Promise<void> {
  await apiJson<null>(`/api/admin/attributes/${attributeId}/values/${valueId}/`, {
    method: 'DELETE',
  });
}

/** Propios **y** heredados de las ancestras, ya resueltos por el backend. */
export async function getCategoryAttributes(
  categoryId: number,
): Promise<CategoryAttribute[]> {
  return apiJson<CategoryAttribute[]>(
    `/api/admin/categories/${categoryId}/attributes/`,
  );
}

/** El enganche se crea siempre en *esta* categoría. 409 si ya lo tiene. */
export async function attachCategoryAttribute(
  categoryId: number,
  fields: { attribute_id: number; is_required: boolean; sort_order: number },
): Promise<CategoryAttribute> {
  return apiJson<CategoryAttribute>(
    `/api/admin/categories/${categoryId}/attributes/`,
    { method: 'POST', ...jsonBody(fields) },
  );
}

/**
 * Cambia obligatorio/orden de un enganche **propio**. Un heredado da 404 con
 * el mensaje de en qué categoría editarlo.
 */
export async function updateCategoryAttribute(
  categoryId: number,
  attributeId: number,
  fields: Partial<{ is_required: boolean; sort_order: number }>,
): Promise<CategoryAttribute> {
  return apiJson<CategoryAttribute>(
    `/api/admin/categories/${categoryId}/attributes/${attributeId}/`,
    { method: 'PATCH', ...jsonBody(fields) },
  );
}

export async function detachCategoryAttribute(
  categoryId: number,
  attributeId: number,
): Promise<void> {
  await apiJson<null>(
    `/api/admin/categories/${categoryId}/attributes/${attributeId}/`,
    { method: 'DELETE' },
  );
}

/**
 * Un atributo que aplica a un producto, con el valor que tenga cargado.
 * `value_id`/`value` en `null` = todavía sin cargar.
 */
export type ProductAttributeField = {
  attribute: Attribute;
  is_required: boolean;
  inherited_from: { id: number; name: string } | null;
  value_id: number | null;
  value: string | null;
};

/** Qué atributos aplican al producto y qué valor tiene cada uno. */
export async function getProductAttributes(
  productId: number,
): Promise<ProductAttributeField[]> {
  return apiJson<ProductAttributeField[]>(
    `/api/admin/products/${productId}/attributes/`,
  );
}

/**
 * Guarda los valores. Toca solo los atributos nombrados; `value_id: null` o
 * `value: ''` borra el que hubiera. Para los `select` va `value_id`; para
 * texto/entero/decimal, `value` con lo que escribió el staff.
 */
export async function setProductAttributes(
  productId: number,
  values: { attribute_id: number; value_id?: number | null; value?: string | null }[],
): Promise<ProductAttributeField[]> {
  return apiJson<ProductAttributeField[]>(
    `/api/admin/products/${productId}/attributes/`,
    { method: 'PUT', ...jsonBody({ values }) },
  );
}

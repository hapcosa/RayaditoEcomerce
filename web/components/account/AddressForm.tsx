'use client';

import { useEffect, useState } from 'react';
import { fetchRegions, type Region } from '@/lib/locations';
import { Field, inputCls } from '@/components/ui/AuthFormWrapper';
import type { AddressFields } from '@/types/checkout';

export const DIRECCION_VACIA: AddressFields = {
  label: '',
  first_name: '',
  last_name: '',
  address_line_1: '',
  city: '',
  country_region: '',
  zipcode: '',
  phone: '',
  is_default: false,
};

interface Props {
  value: AddressFields;
  onChange: (campo: keyof AddressFields, valor: string | boolean) => void;
  /** Prefijo de los `id` de los inputs: puede haber dos formularios en la página. */
  idPrefix?: string;
  /** El nombre de quien recibe se pide aparte en el checkout. */
  ocultarNombre?: boolean;
  /** Etiqueta del check de principal; si falta, no se muestra. */
  labelPrincipal?: string;
}

/**
 * Campos de una dirección chilena, compartidos por el perfil y el checkout.
 *
 * Región sale de un `select` y la comuna de un `datalist` con las comunas de esa
 * región: el envío se cotiza por región/comuna, así que conviene que el texto
 * coincida con el catálogo del backend. Si la lista no carga, ambos siguen
 * siendo texto libre.
 */
export function AddressForm({
  value,
  onChange,
  idPrefix = 'dir',
  ocultarNombre = false,
  labelPrincipal,
}: Props) {
  const [regiones, setRegiones] = useState<Region[]>([]);

  useEffect(() => {
    fetchRegions().then(setRegiones);
  }, []);

  const comunas = regiones.find((r) => r.name === value.country_region)?.communes ?? [];
  const id = (campo: string) => `${idPrefix}-${campo}`;

  return (
    <div className="flex flex-col gap-4">
      {!ocultarNombre && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Nombre de quien recibe" id={id('first_name')}>
            <input id={id('first_name')} type="text" required value={value.first_name}
              onChange={(e) => onChange('first_name', e.target.value)} className={inputCls} />
          </Field>
          <Field label="Apellido" id={id('last_name')}>
            <input id={id('last_name')} type="text" required value={value.last_name}
              onChange={(e) => onChange('last_name', e.target.value)} className={inputCls} />
          </Field>
        </div>
      )}

      <Field label="Dirección" id={id('address_line_1')}>
        <input id={id('address_line_1')} type="text" required value={value.address_line_1}
          onChange={(e) => onChange('address_line_1', e.target.value)} className={inputCls}
          placeholder="Av. Arturo Prat 123, depto. 4B" />
      </Field>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Field label="Región" id={id('country_region')}>
          {regiones.length > 0 ? (
            <select id={id('country_region')} required value={value.country_region}
              onChange={(e) => {
                onChange('country_region', e.target.value);
                onChange('city', '');
              }}
              className={inputCls}>
              <option value="">Elegí una región</option>
              {regiones.map((r) => (
                <option key={r.name} value={r.name}>{r.name}</option>
              ))}
            </select>
          ) : (
            <input id={id('country_region')} type="text" required value={value.country_region}
              onChange={(e) => onChange('country_region', e.target.value)} className={inputCls}
              placeholder="Los Lagos" />
          )}
        </Field>
        <Field label="Ciudad o comuna" id={id('city')}>
          <input id={id('city')} type="text" required value={value.city}
            onChange={(e) => onChange('city', e.target.value)} className={inputCls}
            placeholder="Ancud" list={comunas.length > 0 ? id('comunas') : undefined} />
          {comunas.length > 0 && (
            <datalist id={id('comunas')}>
              {comunas.map((comuna) => <option key={comuna} value={comuna} />)}
            </datalist>
          )}
        </Field>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Field label="Teléfono" id={id('phone')}>
          <input id={id('phone')} type="tel" required value={value.phone}
            onChange={(e) => onChange('phone', e.target.value)} className={inputCls}
            placeholder="+56 9 1234 5678" />
        </Field>
        <Field label="Código postal (opcional)" id={id('zipcode')}>
          <input id={id('zipcode')} type="text" value={value.zipcode}
            onChange={(e) => onChange('zipcode', e.target.value)} className={inputCls} />
        </Field>
      </div>

      <Field label="Nombre para reconocerla (opcional)" id={id('label')}>
        <input id={id('label')} type="text" value={value.label}
          onChange={(e) => onChange('label', e.target.value)} className={inputCls}
          placeholder="Casa, taller, oficina…" />
      </Field>

      {labelPrincipal && (
        <label className="flex items-center gap-2 text-sm text-piedra-700">
          <input type="checkbox" checked={value.is_default}
            onChange={(e) => onChange('is_default', e.target.checked)}
            className="accent-tierra-500" />
          {labelPrincipal}
        </label>
      )}
    </div>
  );
}

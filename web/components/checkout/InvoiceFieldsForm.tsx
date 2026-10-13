'use client';

import { Field, inputCls } from '@/components/ui/AuthFormWrapper';
import type { InvoiceFields } from '@/lib/billing';

interface Props {
  wanted: boolean;
  onWantedChange: (wanted: boolean) => void;
  value: InvoiceFields;
  onChange: (value: InvoiceFields) => void;
}

/** "Necesito factura": por defecto la compra va con boleta. */
export function InvoiceFieldsForm({ wanted, onWantedChange, value, onChange }: Props) {
  function set(campo: keyof InvoiceFields) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      onChange({ ...value, [campo]: e.target.value });
  }

  return (
    <section>
      <label className="flex cursor-pointer items-center gap-3 text-sm text-piedra-800">
        <input
          type="checkbox"
          checked={wanted}
          onChange={(e) => onWantedChange(e.target.checked)}
          className="accent-tierra-500"
        />
        Necesito factura
      </label>

      {wanted && (
        <div className="mt-4 grid grid-cols-1 gap-4 rounded-xl border border-piedra-200 bg-white p-5 sm:grid-cols-2">
          <Field label="RUT de la empresa" id="invoice-rut">
            <input id="invoice-rut" required value={value.rut} onChange={set('rut')}
              className={inputCls} placeholder="76.123.456-7" maxLength={12} />
          </Field>
          <Field label="Razón social" id="invoice-name">
            <input id="invoice-name" required value={value.business_name}
              onChange={set('business_name')} className={inputCls} maxLength={255} />
          </Field>
          <Field label="Giro" id="invoice-activity">
            <input id="invoice-activity" required value={value.activity}
              onChange={set('activity')} className={inputCls} maxLength={255} />
          </Field>
          <Field label="Correo para la factura (opcional)" id="invoice-email">
            <input id="invoice-email" type="email" value={value.email}
              onChange={set('email')} className={inputCls} />
          </Field>
          <Field label="Dirección comercial" id="invoice-address">
            <input id="invoice-address" required value={value.address}
              onChange={set('address')} className={inputCls} maxLength={255} />
          </Field>
          <Field label="Comuna" id="invoice-commune">
            <input id="invoice-commune" required value={value.commune}
              onChange={set('commune')} className={inputCls} maxLength={120} />
          </Field>
        </div>
      )}
    </section>
  );
}

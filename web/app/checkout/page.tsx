'use client';

import Image from 'next/image';
import { mediaUrl } from '@/lib/media';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { useCartStore } from '@/lib/store/cart';
import { syncCart, fetchShippingOptions } from '@/lib/api';
import { processAuthPayment, processGuestPayment, pushCart } from '@/lib/checkout';
import { createAddress, fetchAddresses, resumirDireccion } from '@/lib/addresses';
import { formatCLP } from '@/lib/format';
import { inputCls, Field } from '@/components/ui/AuthFormWrapper';
import { AddressForm, DIRECCION_VACIA } from '@/components/account/AddressForm';
import type { HydratedCartItem, ShippingOption } from '@/types/cart';
import type { Address, AddressFields, CheckoutForm } from '@/types/checkout';

/** Datos de contacto; la dirección vive aparte, en `direccion`. */
type Contacto = Pick<CheckoutForm, 'email' | 'first_name' | 'last_name'>;

const CONTACTO_VACIO: Contacto = { email: '', first_name: '', last_name: '' };

export default function CheckoutPage() {
  const router = useRouter();
  const { access, user } = useAuthStore();
  const { items, clear: clearCart } = useCartStore();

  const [mounted, setMounted] = useState(false);
  const [hydrated, setHydrated] = useState<HydratedCartItem[]>([]);
  const [shipping, setShipping] = useState<ShippingOption[]>([]);
  const [direcciones, setDirecciones] = useState<Address[]>([]);
  /** Dirección guardada elegida; `''` = escribir una nueva. */
  const [elegida, setElegida] = useState<number | ''>('');
  const [direccion, setDireccion] = useState<AddressFields>(DIRECCION_VACIA);
  const [form, setForm] = useState<Contacto>(CONTACTO_VACIO);
  const [selectedShipping, setSelectedShipping] = useState<number | ''>('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => setMounted(true), []);

  // Cargar datos en paralelo al montar.
  useEffect(() => {
    if (!mounted) return;
    if (items.length === 0) return;

    Promise.all([
      syncCart(items),
      fetchShippingOptions(),
      access ? fetchAddresses(access) : Promise.resolve([] as Address[]),
    ]).then(([cart, opts, guardadas]) => {
      setHydrated(cart);
      setShipping(opts);
      if (opts.length > 0) setSelectedShipping(opts[0].id);

      if (user) {
        setForm({ email: user.email, first_name: user.first_name, last_name: user.last_name });
      }
      setDirecciones(guardadas);
      const principal = guardadas.find((d) => d.is_default) ?? guardadas[0];
      if (principal) {
        setElegida(principal.id);
      } else if (user) {
        // Sin libreta se escribe una dirección nueva, con el nombre ya cargado.
        setDireccion((d) => ({
          ...d,
          first_name: user.first_name,
          last_name: user.last_name,
          is_default: true,
        }));
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mounted, access]);

  function setField(k: keyof Contacto) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));
  }

  function setCampoDireccion(campo: keyof AddressFields, valor: string | boolean) {
    setDireccion((d) => ({ ...d, [campo]: valor }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedShipping) { setError('Selecciona una opción de envío'); return; }
    setError('');
    setLoading(true);

    try {
      let preference, orderId;

      if (access) {
        // El pago autenticado arma la orden con el carrito del backend, así que
        // primero se sube el que el navegador tiene guardado.
        await pushCart(access, items.map((i) => ({ product_id: i.product_id, count: i.count })));

        // La orden apunta a una dirección de su libreta, así que la nueva se
        // guarda ahí antes de pagar.
        const profileId = elegida !== ''
          ? elegida
          : (await createAddress(access, {
              ...direccion,
              first_name: direccion.first_name || form.first_name,
              last_name: direccion.last_name || form.last_name,
            })).id;
        ({ preference, orderId } = await processAuthPayment(access, profileId, selectedShipping));
      } else {
        // Invitado: envía items y datos directamente, sin guardar nada.
        const guestItems = hydrated.map((item) => ({
          product: { id: item.product.id },
          count: item.count,
        }));
        ({ preference, orderId } = await processGuestPayment(
          {
            ...form,
            address_line_1: direccion.address_line_1,
            city: direccion.city,
            state_province_region: direccion.country_region,
            postal_zip_code: direccion.zipcode,
            telephone_number: direccion.phone,
            shipping_id: String(selectedShipping),
          },
          guestItems,
        ));
      }

      // Limpiar carrito local y redirigir a MercadoPago.
      clearCart();
      const mpUrl = process.env.NODE_ENV === 'production'
        ? preference.init_point
        : preference.sandbox_init_point;
      window.location.href = mpUrl;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al procesar el pago');
    } finally {
      setLoading(false);
    }
  }

  if (!mounted) {
    return <div className="mx-auto max-w-contenido px-4 sm:px-6 lg:px-10 py-16 text-center text-piedra-500">Cargando…</div>;
  }

  if (items.length === 0) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center gap-6 px-6 py-24 text-center">
        <h1 className="font-serif text-3xl text-piedra-900">Carrito vacío</h1>
        <Link href="/joyas" className="rounded-full bg-tierra-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-tierra-600">
          Ver joyas
        </Link>
      </div>
    );
  }

  const direccionElegida = direcciones.find((d) => d.id === elegida);
  const subtotal = hydrated.reduce((s, i) => s + i.product.price * i.count, 0);
  const selectedOption = shipping.find((s) => s.id === selectedShipping);
  const total = subtotal + (selectedOption?.price ?? 0);

  return (
    <div className="mx-auto max-w-contenido px-4 sm:px-6 lg:px-10 py-10">
      <h1 className="mb-8 font-serif text-3xl font-medium text-piedra-900">Checkout</h1>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-5">

          {/* ── Columna izquierda (3/5): datos del comprador ── */}
          <div className="flex flex-col gap-8 lg:col-span-3">

            {/* Datos de contacto */}
            <section>
              <h2 className="mb-4 font-serif text-xl text-piedra-900">Datos de contacto</h2>
              <div className="flex flex-col gap-4 rounded-xl border border-piedra-200 bg-white p-5">
                {!access && (
                  <Field label="Correo electrónico" id="email">
                    <input id="email" type="email" required value={form.email}
                      onChange={setField('email')} className={inputCls} placeholder="hola@ejemplo.cl" />
                  </Field>
                )}
                {access && user && (
                  <p className="text-sm text-piedra-700">
                    Comprando como <span className="font-medium">{user.email}</span>
                    {' '}·{' '}
                    <Link href="/auth/login" className="text-tierra-600 hover:underline text-xs">no soy yo</Link>
                  </p>
                )}
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Nombre" id="first_name">
                    <input id="first_name" type="text" required value={form.first_name}
                      onChange={setField('first_name')} className={inputCls} />
                  </Field>
                  <Field label="Apellido" id="last_name">
                    <input id="last_name" type="text" required value={form.last_name}
                      onChange={setField('last_name')} className={inputCls} />
                  </Field>
                </div>
              </div>
            </section>

            {/* Dirección */}
            <section>
              <div className="mb-4 flex items-center justify-between gap-4">
                <h2 className="font-serif text-xl text-piedra-900">Dirección de entrega</h2>
                {access && direcciones.length > 0 && (
                  <Link href="/dashboard/direcciones"
                    className="text-xs text-tierra-600 hover:underline">
                    Administrar
                  </Link>
                )}
              </div>

              {/* Con libreta cargada se elige una y no se escribe nada. */}
              {direcciones.length > 0 && (
                <ul className="mb-4 flex flex-col gap-2">
                  {direcciones.map((d) => (
                    <li key={d.id}>
                      <label className={[
                        'flex cursor-pointer items-start gap-3 rounded-xl border p-4 text-sm transition-colors',
                        elegida === d.id
                          ? 'border-tierra-400 bg-tierra-50'
                          : 'border-piedra-200 bg-white hover:border-piedra-300',
                      ].join(' ')}>
                        <input type="radio" name="direccion" checked={elegida === d.id}
                          onChange={() => setElegida(d.id)} className="mt-0.5 accent-tierra-500" />
                        <div className="flex-1">
                          <p className="font-medium text-piedra-900">
                            {d.label || `${d.first_name} ${d.last_name}`}
                            {d.is_default && (
                              <span className="ml-2 rounded-full bg-tierra-100 px-2 py-0.5 text-xs font-medium text-tierra-700">
                                Principal
                              </span>
                            )}
                          </p>
                          <p className="text-piedra-700">{resumirDireccion(d)}</p>
                          {d.phone && <p className="text-xs text-piedra-500">Tel: {d.phone}</p>}
                        </div>
                      </label>
                    </li>
                  ))}
                  <li>
                    <label className={[
                      'flex cursor-pointer items-center gap-3 rounded-xl border p-4 text-sm transition-colors',
                      elegida === ''
                        ? 'border-tierra-400 bg-tierra-50'
                        : 'border-piedra-200 bg-white hover:border-piedra-300',
                    ].join(' ')}>
                      <input type="radio" name="direccion" checked={elegida === ''}
                        onChange={() => setElegida('')} className="accent-tierra-500" />
                      <span className="font-medium text-piedra-900">Usar otra dirección</span>
                    </label>
                  </li>
                </ul>
              )}

              {elegida === '' && (
                <div className="rounded-xl border border-piedra-200 bg-white p-5">
                  <AddressForm
                    value={direccion}
                    onChange={setCampoDireccion}
                    idPrefix="checkout"
                    ocultarNombre
                    labelPrincipal={access ? 'Usar como mi dirección principal' : undefined}
                  />
                  {access && (
                    <p className="mt-4 text-xs text-piedra-500">
                      Esta dirección queda guardada en{' '}
                      <Link href="/dashboard/direcciones" className="text-tierra-600 hover:underline">
                        mis direcciones
                      </Link>{' '}
                      para que no tengas que escribirla de nuevo.
                    </p>
                  )}
                </div>
              )}
            </section>

            {/* Envío */}
            <section>
              <h2 className="mb-4 font-serif text-xl text-piedra-900">Método de envío</h2>
              {shipping.length === 0 ? (
                <p className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                  Todavía no hay métodos de envío configurados. Escribinos y coordinamos
                  el despacho a mano.
                </p>
              ) : (
                <ul className="flex flex-col gap-2">
                  {shipping.map((opt) => (
                    <li key={opt.id}>
                      <label className={[
                        'flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition-colors',
                        selectedShipping === opt.id
                          ? 'border-tierra-400 bg-tierra-50'
                          : 'border-piedra-200 bg-white hover:border-piedra-300',
                      ].join(' ')}>
                        <input type="radio" name="shipping" value={opt.id}
                          checked={selectedShipping === opt.id}
                          onChange={() => setSelectedShipping(opt.id)}
                          className="mt-0.5 accent-tierra-500" />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-piedra-900">{opt.name}</p>
                          <p className="text-xs text-piedra-500">{opt.time_to_delivery}</p>
                        </div>
                        <span className="text-sm font-semibold text-piedra-900">
                          {opt.price === 0 ? 'Gratis' : formatCLP(opt.price)}
                        </span>
                      </label>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>

          {/* ── Columna derecha (2/5): resumen + pagar ── */}
          <aside className="lg:col-span-2">
            <div className="sticky top-24 rounded-2xl border border-piedra-200 bg-white p-6 shadow-sm">
              <h2 className="mb-4 font-serif text-xl text-piedra-900">Tu pedido</h2>

              <ul className="flex flex-col gap-3 border-b border-piedra-200 pb-4">
                {hydrated.map((item) => {
                  const local = items.find((i) => i.product_id === item.product.id);
                  const count = local?.count ?? item.count;
                  return (
                    <li key={item.product.id} className="flex items-center gap-3">
                      <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-lg bg-piedra-100">
                        {item.product.photo && (
                          <Image src={mediaUrl(item.product.photo)} alt={item.product.name}
                            fill sizes="48px" className="object-contain" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="truncate text-xs font-medium text-piedra-900">{item.product.name}</p>
                        <p className="text-xs text-piedra-500">× {count}</p>
                      </div>
                      <span className="text-xs font-semibold text-piedra-900">
                        {formatCLP(item.product.price * count)}
                      </span>
                    </li>
                  );
                })}
              </ul>

              <dl className="mt-4 flex flex-col gap-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-piedra-600">Subtotal</dt>
                  <dd className="font-medium">{formatCLP(subtotal)}</dd>
                </div>
                {selectedOption && (
                  <div className="flex justify-between">
                    <dt className="text-piedra-600">Envío — {selectedOption.name}</dt>
                    <dd className="font-medium">
                      {selectedOption.price === 0 ? 'Gratis' : formatCLP(selectedOption.price)}
                    </dd>
                  </div>
                )}
                <div className="flex justify-between border-t border-piedra-200 pt-3 text-base font-semibold">
                  <dt>Total</dt>
                  <dd>{formatCLP(total)}</dd>
                </div>
              </dl>

              {direccionElegida && (
                <p className="mt-4 border-t border-piedra-100 pt-3 text-xs text-piedra-500">
                  Enviamos a{' '}
                  <span className="text-piedra-700">{resumirDireccion(direccionElegida)}</span>
                </p>
              )}

              {error && (
                <p className="mt-4 rounded-lg bg-red-50 px-4 py-2.5 text-sm text-red-700">{error}</p>
              )}

              <button type="submit" disabled={loading || hydrated.length === 0}
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-full bg-tierra-500 px-6 py-3 text-sm font-medium uppercase tracking-wide text-white transition-colors hover:bg-tierra-600 disabled:bg-piedra-200 disabled:text-piedra-400">
                {loading ? 'Procesando…' : (
                  <>
                    <MpIcon />
                    Pagar con MercadoPago
                  </>
                )}
              </button>

              <p className="mt-2 text-center text-xs text-piedra-400">
                Pagarás en el sitio seguro de MercadoPago
              </p>

              <Link href="/carrito" className="mt-3 block text-center text-xs text-piedra-400 hover:text-tierra-600">
                ← Volver al carrito
              </Link>
            </div>
          </aside>
        </div>
      </form>
    </div>
  );
}

function MpIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4" aria-hidden="true">
      <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm.75 17.25h-1.5v-6h1.5v6zm0-7.5h-1.5V8.25h1.5v1.5z" />
    </svg>
  );
}

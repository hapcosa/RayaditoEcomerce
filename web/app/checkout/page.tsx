'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { useCartStore } from '@/lib/store/cart';
import { syncCart, fetchShippingOptions } from '@/lib/api';
import { fetchProfile, createProfile, processAuthPayment, processGuestPayment } from '@/lib/checkout';
import { formatCLP } from '@/lib/format';
import { inputCls, Field } from '@/components/ui/AuthFormWrapper';
import type { HydratedCartItem, ShippingOption } from '@/types/cart';
import type { SavedProfile, CheckoutForm } from '@/types/checkout';

const EMPTY_FORM: CheckoutForm = {
  email: '',
  first_name: '',
  last_name: '',
  address_line_1: '',
  city: '',
  state_province_region: '',
  postal_zip_code: '',
  telephone_number: '',
  shipping_id: '',
};

export default function CheckoutPage() {
  const router = useRouter();
  const { access, user } = useAuthStore();
  const { items, clear: clearCart } = useCartStore();

  const [mounted, setMounted] = useState(false);
  const [hydrated, setHydrated] = useState<HydratedCartItem[]>([]);
  const [shipping, setShipping] = useState<ShippingOption[]>([]);
  const [profile, setProfile] = useState<SavedProfile | null>(null);
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [form, setForm] = useState<CheckoutForm>(EMPTY_FORM);
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
      access ? fetchProfile(access) : Promise.resolve(null),
    ]).then(([cart, opts, prof]) => {
      setHydrated(cart);
      setShipping(opts);
      if (opts.length > 0) setSelectedShipping(opts[0].id);
      if (prof) {
        setProfile(prof);
        setForm((f) => ({
          ...f,
          email: user?.email ?? '',
          first_name: prof.first_name,
          last_name: prof.last_name,
          address_line_1: prof.address_line_1,
          city: prof.city,
          state_province_region: prof.country_region,
          postal_zip_code: prof.zipcode,
          telephone_number: prof.phone,
        }));
      } else if (user) {
        setForm((f) => ({
          ...f,
          email: user.email,
          first_name: user.first_name,
          last_name: user.last_name,
        }));
        setShowAddressForm(true);
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mounted, access]);

  function setField(k: keyof CheckoutForm) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedShipping) { setError('Selecciona una opción de envío'); return; }
    setError('');
    setLoading(true);

    try {
      let preference, orderId;

      if (access) {
        // Usuario autenticado: necesita perfil guardado en el backend.
        let profileId = profile?.id;
        if (!profileId) {
          const created = await createProfile(access, {
            first_name: form.first_name,
            last_name: form.last_name,
            address_line_1: form.address_line_1,
            city: form.city,
            zipcode: form.postal_zip_code,
            phone: form.telephone_number,
            country_region: form.state_province_region,
          });
          profileId = created.id;
        }
        ({ preference, orderId } = await processAuthPayment(access, profileId, selectedShipping));
      } else {
        // Invitado: envía items directamente.
        const guestItems = hydrated.map((item) => ({
          product: { id: item.product.id },
          count: item.count,
        }));
        ({ preference, orderId } = await processGuestPayment(
          { ...form, shipping_id: String(selectedShipping) },
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
    return <div className="mx-auto max-w-6xl px-6 py-16 text-center text-piedra-500">Cargando…</div>;
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

  const subtotal = hydrated.reduce((s, i) => s + i.product.price * i.count, 0);
  const selectedOption = shipping.find((s) => s.id === selectedShipping);
  const total = subtotal + (selectedOption?.price ?? 0);

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
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
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-serif text-xl text-piedra-900">Dirección de entrega</h2>
                {profile && !showAddressForm && (
                  <button type="button" onClick={() => setShowAddressForm(true)}
                    className="text-xs text-tierra-600 hover:underline">
                    Cambiar
                  </button>
                )}
              </div>

              {profile && !showAddressForm ? (
                <div className="rounded-xl border border-tierra-200 bg-tierra-50/50 p-5 text-sm text-piedra-700">
                  <p className="font-medium">{profile.first_name} {profile.last_name}</p>
                  <p>{profile.address_line_1}</p>
                  <p>{profile.city}{profile.country_region ? `, ${profile.country_region}` : ''} {profile.zipcode}</p>
                  {profile.phone && <p>Tel: {profile.phone}</p>}
                </div>
              ) : (
                <div className="flex flex-col gap-4 rounded-xl border border-piedra-200 bg-white p-5">
                  <Field label="Dirección" id="address">
                    <input id="address" type="text" required value={form.address_line_1}
                      onChange={setField('address_line_1')} className={inputCls}
                      placeholder="Av. Arturo Prat 123" />
                  </Field>
                  <div className="grid grid-cols-2 gap-3">
                    <Field label="Ciudad" id="city">
                      <input id="city" type="text" required value={form.city}
                        onChange={setField('city')} className={inputCls} placeholder="Puerto Montt" />
                    </Field>
                    <Field label="Región" id="region">
                      <input id="region" type="text" required value={form.state_province_region}
                        onChange={setField('state_province_region')} className={inputCls}
                        placeholder="Los Lagos" />
                    </Field>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <Field label="Código postal" id="zip">
                      <input id="zip" type="text" value={form.postal_zip_code}
                        onChange={setField('postal_zip_code')} className={inputCls} />
                    </Field>
                    <Field label="Teléfono" id="phone">
                      <input id="phone" type="tel" required value={form.telephone_number}
                        onChange={setField('telephone_number')} className={inputCls}
                        placeholder="+56 9 1234 5678" />
                    </Field>
                  </div>
                </div>
              )}
            </section>

            {/* Envío */}
            <section>
              <h2 className="mb-4 font-serif text-xl text-piedra-900">Método de envío</h2>
              {shipping.length === 0 ? (
                <p className="text-sm text-piedra-500">Sin opciones de envío disponibles.</p>
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
                          <Image src={item.product.photo} alt={item.product.name}
                            fill sizes="48px" className="object-cover" />
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

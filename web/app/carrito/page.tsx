'use client';

import Image from 'next/image';
import { mediaUrl } from '@/lib/media';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useCartStore } from '@/lib/store/cart';
import { syncCart, fetchShippingOptions } from '@/lib/api';
import { formatCLP } from '@/lib/format';
import type { HydratedCartItem, ShippingOption } from '@/types/cart';

export default function CarritoPage() {
  const { items, removeItem, updateCount, clear } = useCartStore();
  const [hydrated, setHydrated] = useState<HydratedCartItem[]>([]);
  const [shipping, setShipping] = useState<ShippingOption[]>([]);
  const [selectedShipping, setSelectedShipping] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  // Zustand persist necesita un tick para hidratar desde localStorage.
  const [storeReady, setStoreReady] = useState(false);
  useEffect(() => setStoreReady(true), []);

  useEffect(() => {
    if (!storeReady) return;
    if (items.length === 0) {
      setHydrated([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      syncCart(items),
      fetchShippingOptions(),
    ]).then(([cart, opts]) => {
      setHydrated(cart);
      setShipping(opts);
      if (opts.length > 0 && selectedShipping === null) {
        setSelectedShipping(opts[0].id);
      }
    }).catch(() => {
      setHydrated([]);
    }).finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storeReady, items.length]);

  const subtotal = hydrated.reduce(
    (sum, item) => sum + item.product.price * item.count,
    0,
  );
  const selectedOption = shipping.find((s) => s.id === selectedShipping) ?? null;
  const shippingCost = selectedOption?.price ?? 0;
  const total = subtotal + shippingCost;

  // El carrito vacio se resuelve sin pedir nada al backend: se muestra directo,
  // sin pasar por el estado de carga. Hacerlo al reves producia el salto de
  // layout mas grande de la pagina (CLS 0.23, casi en zona mala).
  if (items.length === 0 && storeReady) {
    return (
      <div className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center gap-6 px-6 py-24 text-center">
        <span className="font-manuscrita text-6xl text-piedra-300">✦</span>
        <h1 className="font-serif text-3xl text-piedra-900">Tu carrito está vacío</h1>
        <p className="text-piedra-600">
          Descubre nuestras joyas y piedras artesanales de Chiloé.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link
            href="/joyas"
            className="rounded-full bg-tierra-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-tierra-600"
          >
            Ver joyas
          </Link>
          <Link
            href="/piedras"
            className="rounded-full border border-piedra-300 px-6 py-2.5 text-sm font-medium text-piedra-800 hover:border-agata-500"
          >
            Piedras
          </Link>
        </div>
      </div>
    );
  }

  // Con items, el esqueleto reserva la forma del carrito ya cargado para que la
  // hidratacion no empuje el contenido.
  if (!storeReady || loading) {
    return (
      <div className="mx-auto min-h-[60vh] max-w-6xl px-6 py-10" aria-busy="true">
        <h1 className="mb-8 font-serif text-3xl font-medium text-piedra-900">
          Carrito
        </h1>
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-3">
          <div className="flex flex-col gap-4 lg:col-span-2">
            {[0, 1].map((i) => (
              <div key={i} className="h-28 animate-pulse rounded-2xl bg-piedra-100" />
            ))}
          </div>
          <div className="h-64 animate-pulse rounded-2xl bg-piedra-100" />
        </div>
        <span className="sr-only">Cargando carrito…</span>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="mb-8 font-serif text-3xl font-medium text-piedra-900">
        Carrito
      </h1>

      <div className="grid grid-cols-1 gap-10 lg:grid-cols-3">
        {/* Lista de items */}
        <div className="lg:col-span-2">
          <ul className="flex flex-col divide-y divide-piedra-200">
            {hydrated.map((item) => {
              const local = items.find((i) => i.product_id === item.product.id);
              const count = local?.count ?? item.count;

              return (
                <li key={item.product.id} className="flex gap-4 py-5">
                  {/* Imagen */}
                  <Link
                    href={`/productos/${item.product.slug ?? item.product.id}`}
                    className="relative h-24 w-24 shrink-0 overflow-hidden rounded-xl bg-piedra-100"
                  >
                    {item.product.photo ? (
                      <Image
                        src={mediaUrl(item.product.photo)}
                        alt={item.product.name}
                        fill
                        sizes="96px"
                        className="object-cover"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <span className="font-manuscrita text-2xl text-piedra-300">✦</span>
                      </div>
                    )}
                  </Link>

                  {/* Info */}
                  <div className="flex flex-1 flex-col gap-1">
                    <Link
                      href={`/productos/${item.product.slug ?? item.product.id}`}
                      className="font-medium text-piedra-900 hover:text-tierra-600"
                    >
                      {item.product.name}
                    </Link>
                    <p className="text-sm text-piedra-500">
                      {formatCLP(item.product.price)} c/u
                    </p>

                    {/* Cantidad */}
                    <div className="mt-auto flex items-center gap-3">
                      <div className="flex items-center rounded-full border border-piedra-200">
                        <button
                          onClick={() => updateCount(item.product.id, count - 1)}
                          disabled={count <= 1}
                          className="flex h-8 w-8 items-center justify-center rounded-full text-piedra-600 transition-colors hover:bg-piedra-100 disabled:opacity-30"
                          aria-label="Quitar uno"
                        >
                          −
                        </button>
                        <span className="w-8 text-center text-sm font-medium">
                          {count}
                        </span>
                        <button
                          onClick={() => updateCount(item.product.id, count + 1)}
                          disabled={count >= item.product.available_stock}
                          className="flex h-8 w-8 items-center justify-center rounded-full text-piedra-600 transition-colors hover:bg-piedra-100 disabled:opacity-30"
                          aria-label="Agregar uno"
                        >
                          +
                        </button>
                      </div>

                      <button
                        onClick={() => removeItem(item.product.id)}
                        className="text-xs text-piedra-400 hover:text-red-500"
                      >
                        Eliminar
                      </button>
                    </div>
                  </div>

                  {/* Subtotal */}
                  <div className="text-right">
                    <p className="font-semibold text-piedra-900">
                      {formatCLP(item.product.price * count)}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>

          <button
            onClick={clear}
            className="mt-4 text-xs text-piedra-400 hover:text-red-500"
          >
            Vaciar carrito
          </button>
        </div>

        {/* Resumen */}
        <aside className="rounded-2xl border border-piedra-200 bg-white p-6 shadow-sm self-start lg:sticky lg:top-24">
          <h2 className="font-serif text-xl font-medium text-piedra-900">Resumen</h2>

          <dl className="mt-4 flex flex-col gap-2 border-b border-piedra-200 pb-4">
            <div className="flex justify-between text-sm">
              <dt className="text-piedra-600">Subtotal</dt>
              <dd className="font-medium text-piedra-900">{formatCLP(subtotal)}</dd>
            </div>
          </dl>

          {/* Envío */}
          {shipping.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-sm font-semibold text-piedra-700">Envío</p>
              <ul className="flex flex-col gap-2">
                {shipping.map((opt) => (
                  <li key={opt.id}>
                    <label className="flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition-colors hover:border-tierra-300"
                      style={{
                        borderColor: selectedShipping === opt.id ? 'rgb(173 92 58)' : undefined,
                        background: selectedShipping === opt.id ? 'rgb(250 243 238)' : undefined,
                      }}>
                      <input
                        type="radio"
                        name="shipping"
                        value={opt.id}
                        checked={selectedShipping === opt.id}
                        onChange={() => setSelectedShipping(opt.id)}
                        className="mt-0.5 accent-tierra-500"
                      />
                      <div className="flex-1 text-sm">
                        <p className="font-medium text-piedra-900">{opt.name}</p>
                        <p className="text-piedra-500">{opt.time_to_delivery}</p>
                      </div>
                      <span className="text-sm font-semibold text-piedra-900">
                        {opt.price === 0 ? 'Gratis' : formatCLP(opt.price)}
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <dl className="mt-4 flex flex-col gap-2">
            {selectedOption && (
              <div className="flex justify-between text-sm">
                <dt className="text-piedra-600">Envío — {selectedOption.name}</dt>
                <dd className="font-medium text-piedra-900">
                  {selectedOption.price === 0 ? 'Gratis' : formatCLP(selectedOption.price)}
                </dd>
              </div>
            )}
            <div className="flex justify-between border-t border-piedra-200 pt-3 text-base font-semibold">
              <dt className="text-piedra-900">Total</dt>
              <dd className="text-piedra-900">{formatCLP(total)}</dd>
            </div>
          </dl>

          <Link
            href="/checkout"
            className="mt-6 block w-full rounded-full bg-tierra-500 px-6 py-3 text-center text-sm font-medium uppercase tracking-wide text-white hover:bg-tierra-600"
          >
            Ir al checkout
          </Link>
          <p className="mt-2 text-center text-xs text-piedra-400">
            Pago seguro con MercadoPago
          </p>
        </aside>
      </div>
    </div>
  );
}

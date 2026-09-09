'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import {
  createAddress,
  deleteAddress,
  fetchAddresses,
  setDefaultAddress,
  updateAddress,
} from '@/lib/addresses';
import { AddressForm, DIRECCION_VACIA } from '@/components/account/AddressForm';
import { submitCls } from '@/components/ui/AuthFormWrapper';
import type { Address, AddressFields } from '@/types/checkout';

export default function DireccionesPage() {
  const router = useRouter();
  const { access, user } = useAuthStore();

  const [mounted, setMounted] = useState(false);
  const [cargando, setCargando] = useState(true);
  const [direcciones, setDirecciones] = useState<Address[]>([]);
  /** `null` = formulario cerrado; `'nueva'` = alta; un id = edición. */
  const [editando, setEditando] = useState<number | 'nueva' | null>(null);
  const [borrador, setBorrador] = useState<AddressFields>(DIRECCION_VACIA);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!mounted) return;
    if (!access) router.replace('/auth/login?next=/dashboard/direcciones');
  }, [mounted, access, router]);

  const recargar = useCallback(async (token: string) => {
    setDirecciones(await fetchAddresses(token));
    setCargando(false);
  }, []);

  useEffect(() => {
    if (!mounted || !access) return;
    recargar(access);
  }, [mounted, access, recargar]);

  function abrirNueva() {
    setError('');
    setBorrador({
      ...DIRECCION_VACIA,
      first_name: user?.first_name ?? '',
      last_name: user?.last_name ?? '',
      // La primera dirección queda principal de todas formas; marcarlo evita
      // que el check aparezca desmarcado y confunda.
      is_default: direcciones.length === 0,
    });
    setEditando('nueva');
  }

  function abrirEdicion(direccion: Address) {
    setError('');
    const { id: _id, ...campos } = direccion;
    setBorrador(campos);
    setEditando(direccion.id);
  }

  function setCampo(campo: keyof AddressFields, valor: string | boolean) {
    setBorrador((b) => ({ ...b, [campo]: valor }));
  }

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    if (!access) return;
    setError('');
    setGuardando(true);
    try {
      if (editando === 'nueva') await createAddress(access, borrador);
      else if (typeof editando === 'number') await updateAddress(access, editando, borrador);
      setEditando(null);
      await recargar(access);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar la dirección');
    } finally {
      setGuardando(false);
    }
  }

  async function accion(fn: () => Promise<unknown>) {
    if (!access) return;
    setError('');
    try {
      await fn();
      await recargar(access);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo completar la acción');
    }
  }

  if (!mounted || !access) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16 text-center text-piedra-500">Cargando…</div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <Link href="/dashboard" className="text-xs uppercase tracking-wide text-tierra-600 hover:underline">
        ← Mi cuenta
      </Link>
      <h1 className="mt-3 font-serif text-3xl font-medium text-piedra-900">Mis direcciones</h1>
      <p className="mt-1 text-sm text-piedra-500">
        Las direcciones que guardes acá se pueden elegir al pagar, sin escribirlas de nuevo.
      </p>

      {error && (
        <p className="mt-6 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {cargando ? (
        <p className="mt-8 text-sm text-piedra-500">Cargando direcciones…</p>
      ) : (
        <ul className="mt-8 flex flex-col gap-4">
          {direcciones.map((direccion) => (
            <li key={direccion.id}
              className="rounded-xl border border-piedra-200 bg-white p-5 text-sm text-piedra-700">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-medium text-piedra-900">
                    {direccion.label || `${direccion.first_name} ${direccion.last_name}`}
                    {direccion.is_default && (
                      <span className="ml-2 rounded-full bg-tierra-100 px-2 py-0.5 text-xs font-medium text-tierra-700">
                        Principal
                      </span>
                    )}
                  </p>
                  <p className="mt-1">{direccion.first_name} {direccion.last_name}</p>
                  <p>{direccion.address_line_1}</p>
                  <p>
                    {direccion.city}
                    {direccion.country_region ? `, ${direccion.country_region}` : ''}
                    {direccion.zipcode ? ` · ${direccion.zipcode}` : ''}
                  </p>
                  {direccion.phone && <p>Tel: {direccion.phone}</p>}
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1 text-xs">
                  <button type="button" onClick={() => abrirEdicion(direccion)}
                    className="text-tierra-600 hover:underline">
                    Editar
                  </button>
                  {!direccion.is_default && (
                    <button type="button"
                      onClick={() => accion(() => setDefaultAddress(access, direccion.id))}
                      className="text-piedra-500 hover:text-tierra-600">
                      Usar como principal
                    </button>
                  )}
                  <button type="button"
                    onClick={() => {
                      if (confirm('¿Borrar esta dirección? Tus pedidos anteriores no se tocan.')) {
                        accion(() => deleteAddress(access, direccion.id));
                      }
                    }}
                    className="text-piedra-400 hover:text-red-600">
                    Borrar
                  </button>
                </div>
              </div>
            </li>
          ))}

          {direcciones.length === 0 && editando === null && (
            <li className="rounded-xl border border-dashed border-piedra-300 p-6 text-center text-sm text-piedra-500">
              Todavía no guardaste ninguna dirección.
            </li>
          )}
        </ul>
      )}

      {editando === null ? (
        <button type="button" onClick={abrirNueva}
          className="mt-6 rounded-full border border-tierra-300 px-5 py-2 text-sm font-medium text-tierra-700 hover:bg-tierra-50">
          Agregar dirección
        </button>
      ) : (
        <form onSubmit={guardar} className="mt-8 rounded-xl border border-piedra-200 bg-white p-5">
          <h2 className="mb-4 font-serif text-xl text-piedra-900">
            {editando === 'nueva' ? 'Nueva dirección' : 'Editar dirección'}
          </h2>
          <AddressForm value={borrador} onChange={setCampo} idPrefix="perfil"
            labelPrincipal="Usar como dirección principal" />
          <div className="mt-6 flex items-center gap-3">
            <button type="submit" disabled={guardando} className={`${submitCls} sm:w-auto sm:px-8`}>
              {guardando ? 'Guardando…' : 'Guardar'}
            </button>
            <button type="button" onClick={() => setEditando(null)}
              className="text-sm text-piedra-500 hover:text-piedra-800">
              Cancelar
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

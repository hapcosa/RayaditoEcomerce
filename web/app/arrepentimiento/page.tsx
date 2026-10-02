import type { Metadata } from 'next';
import Link from 'next/link';
import { Suspense } from 'react';
import { WithdrawalForm } from '@/components/orders/WithdrawalForm';

export const metadata: Metadata = {
  title: 'Arrepentimiento de compra (derecho a retracto)',
  description:
    'Retráctate de una compra en Piedras Rayadito dentro de los 10 días siguientes a recibir tu pedido.',
};

export default function ArrepentimientoPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="font-serif text-4xl font-medium text-piedra-900">
        Arrepentimiento de compra
      </h1>
      <p className="mt-2 text-sm text-piedra-500">Derecho a retracto · Ley 19.496, art. 3 bis</p>

      <div className="mt-8 flex flex-col gap-4 text-sm leading-relaxed text-piedra-700">
        <p>
          Si compraste en nuestra tienda en línea, tienes derecho a retractarte
          de la compra <strong>dentro de los 10 días siguientes a la recepción
          del producto</strong>, sin tener que explicar por qué.
        </p>
        <ul className="list-disc space-y-1 pl-5">
          <li>El producto debe estar sin uso y con su embalaje original.</li>
          <li>
            Las piezas <strong>hechas a medida</strong> según tus especificaciones
            (encargos personalizados) no tienen derecho a retracto.
          </li>
          <li>
            Si no te llegó el correo de confirmación de tu compra, el plazo es
            de 90 días.
          </li>
          <li>
            Una vez que recibamos el producto, te devolvemos lo pagado.
          </li>
        </ul>
        <p>
          El retracto es distinto de la garantía legal: si tu pieza llegó con
          una falla, escríbenos desde la página de contacto.
        </p>
      </div>

      <section className="mt-10 rounded-2xl border border-piedra-200 p-6">
        <h2 className="font-serif text-2xl text-piedra-900">Solicitar el retracto</h2>
        <p className="mt-2 mb-6 text-sm text-piedra-600">
          El número de pedido aparece en el correo de confirmación y en{' '}
          <Link href="/pedidos" className="text-tierra-600 hover:underline">
            Mis pedidos
          </Link>
          .
        </p>
        <Suspense fallback={null}>
          <WithdrawalForm />
        </Suspense>
      </section>
    </div>
  );
}

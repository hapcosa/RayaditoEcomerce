import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Preguntas frecuentes',
  description:
    'Dudas sobre compras, envíos, pagos y las piezas artesanales de Piedras Rayadito.',
};

const FAQS: { q: string; a: string }[] = [
  {
    q: '¿Las piezas son únicas?',
    a: 'Sí. Cada joya y cada piedra se trabaja a mano, una por una. Por eso puede haber pequeñas variaciones de color, forma y textura respecto de las fotografías.',
  },
  {
    q: '¿Cómo se realizan los pagos?',
    a: 'Los pagos se procesan a través de MercadoPago. Todos los precios están en pesos chilenos (CLP).',
  },
  {
    q: '¿Cómo y cuándo llega mi pedido?',
    a: 'Despachamos mediante Starken u otras opciones que se informan durante el checkout. Los plazos dependen del destino dentro de Chile.',
  },
  {
    q: '¿Puedo encargar una pieza a medida?',
    a: 'Sí, según disponibilidad de material. Escríbenos por el buzón de contacto contándonos qué buscas y te respondemos.',
  },
  {
    q: '¿Cómo cuido mi joya con piedra?',
    a: 'Evita el contacto con perfumes, cremas y agua de mar. Guárdala seca y, para limpiarla, usa un paño suave. Así conserva su brillo por años.',
  },
];

export default function FaqPage() {
  return (
    <div className="mx-auto max-w-prosa px-6 py-20">
      <p className="font-manuscrita text-2xl text-tierra-600">¿dudas?</p>
      <h1 className="mt-3 font-serif text-5xl font-medium leading-tight text-piedra-900">
        Preguntas frecuentes
      </h1>

      <div className="mt-10 flex flex-col divide-y divide-piedra-200 border-y border-piedra-200">
        {FAQS.map(({ q, a }) => (
          <details key={q} className="group py-5">
            <summary className="flex cursor-pointer items-center justify-between gap-4 font-serif text-xl text-piedra-900 marker:content-['']">
              {q}
              <span className="text-tierra-500 transition-transform group-open:rotate-45" aria-hidden>
                +
              </span>
            </summary>
            <p className="mt-3 leading-relaxed text-piedra-700">{a}</p>
          </details>
        ))}
      </div>

      <p className="mt-10 text-piedra-700">
        ¿No encuentras tu respuesta?{' '}
        <Link href="/contacto" className="text-tierra-600 underline underline-offset-4 hover:text-tierra-700">
          Escríbenos
        </Link>
        .
      </p>
    </div>
  );
}

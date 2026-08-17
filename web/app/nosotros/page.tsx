import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Nosotros',
  description:
    'La historia de Piedras Rayadito: joyería y lapidación artesanal de piedras de Chiloé.',
};

export default function NosotrosPage() {
  return (
    <div className="mx-auto max-w-prosa px-6 py-20">
      <p className="font-manuscrita text-2xl text-tierra-600">nuestra historia</p>
      <h1 className="mt-3 font-serif text-5xl font-medium leading-tight text-piedra-900">
        Piedras de Chiloé, hechas joya
      </h1>

      <div className="mt-10 flex flex-col gap-6 text-lg leading-relaxed text-piedra-700">
        <p>
          Piedras Rayadito nace en el sur de Chile, en las playas de la isla de
          Chiloé, donde recogemos ágatas, jaspes y minerales pulidos por el mar.
          Cada piedra guarda millones de años de historia; nuestro trabajo es
          revelarla.
        </p>
        <p>
          Lapidamos y montamos cada pieza a mano, una por una. No hacemos
          producción en serie: lo que ves es único, y por eso puede tener
          pequeñas variaciones de color y forma respecto de las fotografías. Esa
          es, precisamente, la huella de lo artesanal.
        </p>
        <p>
          Trabajamos con oficio, paciencia y respeto por el material. Creemos en
          objetos que duran, que se heredan y que cuentan de dónde vienen.
        </p>
      </div>

      <div className="mt-12 flex flex-wrap gap-4">
        <Link
          href="/joyas"
          className="rounded-full bg-tierra-500 px-7 py-3 text-sm font-medium uppercase tracking-wide text-piedra-50 transition-colors hover:bg-tierra-600"
        >
          Ver joyas
        </Link>
        <Link
          href="/contacto"
          className="rounded-full border border-piedra-300 px-7 py-3 text-sm font-medium uppercase tracking-wide text-piedra-800 transition-colors hover:border-agata-500 hover:text-agata-600"
        >
          Contacto
        </Link>
      </div>
    </div>
  );
}

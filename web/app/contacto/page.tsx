import type { Metadata } from 'next';
import { SuggestionForm } from '@/components/layout/SuggestionForm';

export const metadata: Metadata = {
  title: 'Contacto',
  description:
    'Escríbenos: dudas, encargos a medida, reclamos o felicitaciones para Piedras Rayadito.',
};

const CONTACT_EMAIL =
  process.env.NEXT_PUBLIC_CONTACT_EMAIL ?? 'contacto@piedrasrayadito.cl';
const INSTAGRAM_URL = process.env.NEXT_PUBLIC_INSTAGRAM_URL ?? '';
const WHATSAPP_URL = process.env.NEXT_PUBLIC_WHATSAPP_URL ?? '';

export default function ContactoPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-20">
      <p className="font-manuscrita text-2xl text-tierra-600">hablemos</p>
      <h1 className="mt-3 font-serif text-5xl font-medium leading-tight text-piedra-900">
        Contacto
      </h1>
      <p className="mt-6 max-w-prosa text-lg leading-relaxed text-piedra-700">
        ¿Tienes una duda, quieres encargar una pieza a medida o simplemente
        contarnos algo? Escríbenos y te respondemos a la brevedad.
      </p>

      <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div className="rounded-2xl border border-piedra-200 p-6">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-piedra-600">
            Correo
          </h2>
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className="mt-2 block text-piedra-900 hover:text-tierra-600"
          >
            {CONTACT_EMAIL}
          </a>
        </div>
        <div className="rounded-2xl border border-piedra-200 p-6">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-piedra-600">
            Redes
          </h2>
          <div className="mt-2 flex flex-col gap-1">
            {INSTAGRAM_URL || WHATSAPP_URL ? (
              <>
                {INSTAGRAM_URL && (
                  <a
                    href={INSTAGRAM_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-piedra-900 hover:text-tierra-600"
                  >
                    Instagram
                  </a>
                )}
                {WHATSAPP_URL && (
                  <a
                    href={WHATSAPP_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-piedra-900 hover:text-tierra-600"
                  >
                    WhatsApp
                  </a>
                )}
              </>
            ) : (
              <span className="text-sm text-piedra-500">Próximamente</span>
            )}
          </div>
        </div>
      </div>

      {/* Buzón — panel oscuro para el formulario (mismo estilo que el footer). */}
      <section className="mt-10 rounded-2xl bg-piedra-900 p-8 text-piedra-300">
        <h2 className="font-serif text-2xl text-piedra-50">Envíanos un mensaje</h2>
        <p className="mt-1 text-sm text-piedra-400">
          Sugerencia, reclamo, felicitación o consulta: cuéntanos.
        </p>
        <div className="mt-6">
          <SuggestionForm />
        </div>
      </section>
    </div>
  );
}

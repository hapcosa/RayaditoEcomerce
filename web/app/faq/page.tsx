import type { Metadata } from 'next';
import Link from 'next/link';
import { FAQS, faqDescription } from '@/content/faq';

export const metadata: Metadata = {
  title: 'Preguntas frecuentes',
  description: faqDescription,
};

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

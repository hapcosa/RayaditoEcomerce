import type { Metadata } from 'next';
import Link from 'next/link';
import { nosotros } from '@/content/nosotros';
import { catalogHref, primaryCatalog } from '@/lib/store-config';

export const metadata: Metadata = {
  title: 'Nosotros',
  description: nosotros.description,
};

export default function NosotrosPage() {
  return (
    <div className="mx-auto max-w-prosa px-6 py-20">
      <p className="font-manuscrita text-2xl text-tierra-600">{nosotros.eyebrow}</p>
      <h1 className="mt-3 font-serif text-5xl font-medium leading-tight text-piedra-900">
        {nosotros.title}
      </h1>

      <div className="mt-10 flex flex-col gap-6 text-lg leading-relaxed text-piedra-700">
        {nosotros.paragraphs.map((text) => (
          <p key={text}>{text}</p>
        ))}
      </div>

      <div className="mt-12 flex flex-wrap gap-4">
        <Link
          href={catalogHref(primaryCatalog)}
          className="rounded-full bg-tierra-500 px-7 py-3 text-sm font-medium uppercase tracking-wide text-piedra-50 transition-colors hover:bg-tierra-600"
        >
          Ver {primaryCatalog.label.toLowerCase()}
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

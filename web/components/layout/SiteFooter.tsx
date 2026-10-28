import Link from 'next/link';
import { SuggestionForm } from './SuggestionForm';
import { catalogHref, catalogs, contact, store } from '@/lib/store-config';

// Contacto y redes: store.json, con override por entorno (ver lib/store.ts).
const CONTACT_EMAIL = contact.email;
const INSTAGRAM_URL = contact.instagramUrl;
const WHATSAPP_URL = contact.whatsappUrl;

const NAV_LINKS = [
  ...catalogs.map((c) => ({ href: catalogHref(c), label: c.label })),
  { href: '/nosotros', label: 'Nosotros' },
  { href: '/faq', label: 'Preguntas frecuentes' },
  { href: '/contacto', label: 'Contacto' },
  { href: '/dashboard', label: 'Mi cuenta' },
];

const LEGAL_LINKS = [
  { href: '/terminos', label: 'Términos y condiciones' },
  { href: '/privacidad', label: 'Política de privacidad' },
  { href: '/arrepentimiento', label: 'Arrepentimiento de compra' },
];

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-20 border-t border-piedra-700 bg-piedra-900 text-piedra-300">
      <div className="mx-auto grid max-w-contenido grid-cols-1 gap-10 px-4 sm:px-6 lg:px-10 py-14 md:grid-cols-2 lg:grid-cols-4">
        {/* Marca */}
        <div className="flex flex-col gap-3">
          <span className="font-manuscrita text-2xl text-tierra-300">{store.name}</span>
          <p className="text-sm leading-relaxed text-piedra-400">{store.web.description}</p>
        </div>

        {/* Navegación */}
        <nav aria-label="Navegación del pie" className="flex flex-col gap-3">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-piedra-200">
            Explorar
          </h2>
          <ul className="flex flex-col gap-2 text-sm">
            {NAV_LINKS.map(({ href, label }) => (
              <li key={href}>
                <Link href={href} className="hover:text-tierra-300">
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* Contacto + redes */}
        <div className="flex flex-col gap-3">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-piedra-200">
            Contacto
          </h2>
          <a href={`mailto:${CONTACT_EMAIL}`} className="text-sm hover:text-tierra-300">
            {CONTACT_EMAIL}
          </a>
          <div className="mt-1 flex flex-col gap-2 text-sm">
            {INSTAGRAM_URL && (
              <a
                href={INSTAGRAM_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-tierra-300"
              >
                Instagram
              </a>
            )}
            {WHATSAPP_URL && (
              <a
                href={WHATSAPP_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-tierra-300"
              >
                WhatsApp
              </a>
            )}
          </div>
          <ul className="mt-2 flex flex-col gap-2 text-sm">
            {LEGAL_LINKS.map(({ href, label }) => (
              <li key={href}>
                <Link href={href} className="text-piedra-400 hover:text-tierra-300">
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Buzón de sugerencias */}
        <div className="flex flex-col gap-3">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-piedra-200">
            Buzón de sugerencias
          </h2>
          <p className="text-sm text-piedra-400">
            ¿Una idea, un reclamo o una felicitación? Escríbenos.
          </p>
          <SuggestionForm />
        </div>
      </div>

      <div className="border-t border-piedra-800">
        <div className="mx-auto max-w-contenido px-4 sm:px-6 lg:px-10 py-6 text-xs text-piedra-400">
          © {year} {store.name} · {store.web.location}. Todos los derechos reservados.
        </div>
      </div>
    </footer>
  );
}

import Link from 'next/link';
import { SuggestionForm } from './SuggestionForm';

// Contacto y redes son configurables por entorno. Dominio/email definitivos
// llegan en Fase 7; los defaults son placeholders hasta entonces.
const CONTACT_EMAIL =
  process.env.NEXT_PUBLIC_CONTACT_EMAIL ?? 'contacto@piedrasrayadito.cl';
const INSTAGRAM_URL = process.env.NEXT_PUBLIC_INSTAGRAM_URL ?? '';
const WHATSAPP_URL = process.env.NEXT_PUBLIC_WHATSAPP_URL ?? '';

const NAV_LINKS = [
  { href: '/joyas', label: 'Joyas' },
  { href: '/piedras', label: 'Piedras' },
  { href: '/carrito', label: 'Carrito' },
  { href: '/dashboard', label: 'Mi cuenta' },
];

const LEGAL_LINKS = [
  { href: '/terminos', label: 'Términos y condiciones' },
  { href: '/privacidad', label: 'Política de privacidad' },
];

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-20 border-t border-piedra-700 bg-piedra-900 text-piedra-300">
      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-10 px-6 py-14 md:grid-cols-2 lg:grid-cols-4">
        {/* Marca */}
        <div className="flex flex-col gap-3">
          <span className="font-manuscrita text-2xl text-tierra-300">Piedras Rayadito</span>
          <p className="text-sm leading-relaxed text-piedra-400">
            Joyería artesanal y lapidación de piedras de Chiloé. Piezas únicas
            hechas a mano en el sur de Chile.
          </p>
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
        <div className="mx-auto max-w-6xl px-6 py-6 text-xs text-piedra-500">
          © {year} Piedras Rayadito · Chiloé, Chile. Todos los derechos reservados.
        </div>
      </div>
    </footer>
  );
}

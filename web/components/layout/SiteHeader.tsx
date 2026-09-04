'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { CartBadge } from './CartBadge';
import { AuthNav } from './AuthNav';

const NAV = [
  { href: '/joyas', label: 'Joyas' },
  { href: '/piedras', label: 'Piedras' },
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-piedra-200 bg-piedra-50/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="shrink-0" aria-label="Piedras Rayadito — inicio">
          {/* Logo horizontal (pájaro + marca denominativa), ratio 2.72:1.
              `alt` conserva el nombre para lectores de pantalla. */}
          <Image
            src="/logo-rayadito.png"
            alt="Piedras Rayadito"
            width={800}
            height={294}
            priority
            className="h-9 w-auto sm:h-11"
          />
        </Link>

        <nav className="flex items-center gap-6">
          {NAV.map(({ href, label }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={[
                  'text-sm font-medium uppercase tracking-wide transition-colors',
                  active
                    ? 'text-tierra-600 underline underline-offset-4'
                    : 'text-piedra-700 hover:text-tierra-600',
                ].join(' ')}
              >
                {label}
              </Link>
            );
          })}
          <CartBadge />
          <AuthNav />
        </nav>
      </div>
    </header>
  );
}

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Panel de ventas',
  // El panel es interno: nunca debe aparecer en un buscador. El control de
  // acceso real lo hace el backend (`IsAdminUser` en /api/admin/stats/); esto
  // solo evita que la URL se indexe.
  robots: { index: false, follow: false },
};

export default function PanelLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

import { ImageResponse } from 'next/og';
import { fetchProduct } from '@/lib/api';
import { formatCLP } from '@/lib/format';

// Ruta dinámica: se renderiza por petición, nunca en build.
export const runtime = 'nodejs';

export const alt = 'Piedras Rayadito — pieza artesanal';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

// Paleta artesanal (piedra / tierra / ágata), espejo de globals.css.
const PIEDRA_50 = 'rgb(250, 249, 246)';
const PIEDRA_500 = 'rgb(148, 138, 122)';
const PIEDRA_900 = 'rgb(38, 35, 31)';
const TIERRA_600 = 'rgb(148, 74, 45)';
const AGATA_500 = 'rgb(203, 135, 47)';

/**
 * Carga la variante serif (Cormorant Garamond) solo para el texto pedido.
 * Es una llamada en tiempo de petición; si falla, se usa la fuente por defecto.
 */
async function loadSerif(text: string): Promise<ArrayBuffer | null> {
  try {
    const cssUrl = `https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&text=${encodeURIComponent(
      text,
    )}`;
    const css = await (
      await fetch(cssUrl, {
        headers: {
          // Sin este UA, Google devuelve WOFF2 (no soportado por Satori).
          'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
      })
    ).text();
    const src = css.match(/src:\s*url\((.+?)\)\s*format/);
    if (!src) return null;
    const font = await fetch(src[1]);
    if (!font.ok) return null;
    return await font.arrayBuffer();
  } catch {
    return null;
  }
}

interface Props {
  params: { slug: string };
}

export default async function Image({ params }: Props) {
  let name = 'Piezas únicas de Chiloé';
  let price: string | null = null;
  let typeLabel = 'Artesanía';

  try {
    const product = await fetchProduct(params.slug);
    name = product.name;
    price = formatCLP(product.price);
    typeLabel = product.product_type === 'piedra' ? 'Piedra lapidada' : 'Joya artesanal';
  } catch {
    // Cae en los valores por defecto (producto no encontrado / API caída).
  }

  const serifText = `${name}${price ?? ''}${typeLabel}Piedras Rayadito`;
  const serif = await loadSerif(serifText);

  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: 64,
          backgroundColor: PIEDRA_50,
          backgroundImage:
            'radial-gradient(circle at 85% 15%, rgba(203,135,47,0.18), transparent 45%)',
          fontFamily: serif ? 'Cormorant' : 'serif',
        }}
      >
        {/* Marco artesanal */}
        <div
          style={{
            position: 'absolute',
            top: 28,
            left: 28,
            right: 28,
            bottom: 28,
            border: `2px solid ${AGATA_500}`,
            borderRadius: 18,
          }}
        />

        {/* Cabecera: marca */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            fontSize: 30,
            letterSpacing: 2,
            textTransform: 'uppercase',
            color: TIERRA_600,
          }}
        >
          Piedras Rayadito
        </div>

        {/* Cuerpo: nombre + tipo */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div
            style={{
              fontSize: 24,
              letterSpacing: 3,
              textTransform: 'uppercase',
              color: PIEDRA_500,
            }}
          >
            {typeLabel}
          </div>
          <div
            style={{
              display: 'flex',
              fontSize: name.length > 40 ? 68 : 84,
              lineHeight: 1.05,
              color: PIEDRA_900,
            }}
          >
            {name}
          </div>
        </div>

        {/* Pie: precio */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {price && (
            <div style={{ fontSize: 56, fontWeight: 600, color: TIERRA_600 }}>
              {price}
            </div>
          )}
          <div style={{ fontSize: 26, color: PIEDRA_500 }}>
            Joyería y lapidación · Chiloé
          </div>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: serif
        ? [{ name: 'Cormorant', data: serif, style: 'normal', weight: 600 }]
        : [],
    },
  );
}

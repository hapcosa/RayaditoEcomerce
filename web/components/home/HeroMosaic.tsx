import Image from 'next/image';
import { mediaUrl } from '@/lib/media';
import type { HeroImage } from '@/types/homepage';

/**
 * Mosaico escalonado de la portada (de 1 a 7 fotos; la dueña elige el tope
 * entre 3 y 7 desde la app, ver `homepage.HomepageSettings`).
 *
 * No es una grilla pareja a propósito: cada foto tiene su propio ancho y su
 * desfase vertical, así que el conjunto se lee como una composición y no como
 * un carrete. No se solapan porque el solape tapaba el pie de foto de la
 * anterior.
 *
 * Cada foto se muestra ENTERA, con la proporción que trae. Antes cada posición
 * imponía la suya y `object-cover` recortaba lo que sobraba: las fotos
 * verticales del taller quedaban decapitadas. El escalonado ya lo dan los
 * anchos y los desfases; forzar la proporción solo costaba encuadre.
 *
 * Escritorio: hay una composición dibujada para cada cantidad (`ESCRITORIO`),
 * en filas de 12 columnas. Más de 3 fotos arma una segunda fila que no repite
 * la primera, así no queda una cuadrícula.
 *
 * Móvil: hasta 3 fotos se alternan a izquierda y derecha con anchos distintos.
 * Con más, apiladas así la portada se volvía un rollo de siete pantallas: la
 * primera queda grande y el resto pasa a dos columnas desfasadas.
 *
 * Las clases van escritas enteras (nada de `lg:col-span-${n}`): Tailwind solo
 * genera las que encuentra literalmente en el código.
 */

type Celda = { clase: string; columnas: number };

const FILA_PRINCIPAL: Celda[] = [
  { clase: 'lg:col-span-5 lg:mt-0', columnas: 5 },
  { clase: 'lg:col-span-4 lg:mt-20', columnas: 4 },
  { clase: 'lg:col-span-3 lg:mt-8', columnas: 3 },
];

const ESCRITORIO: Record<number, Celda[]> = {
  1: [{ clase: 'lg:col-span-6 lg:col-start-4 lg:mt-0', columnas: 6 }],
  2: [
    { clase: 'lg:col-span-6 lg:col-start-2 lg:mt-0', columnas: 6 },
    { clase: 'lg:col-span-4 lg:mt-16', columnas: 4 },
  ],
  3: FILA_PRINCIPAL,
  // Cuatro en una fila, cada una a su altura.
  4: [
    { clase: 'lg:col-span-3 lg:mt-0', columnas: 3 },
    { clase: 'lg:col-span-3 lg:mt-16', columnas: 3 },
    { clase: 'lg:col-span-3 lg:mt-6', columnas: 3 },
    { clase: 'lg:col-span-3 lg:mt-20', columnas: 3 },
  ],
  // La fila de 3 y debajo dos centradas.
  5: [
    ...FILA_PRINCIPAL,
    { clase: 'lg:col-span-4 lg:col-start-3 lg:mt-6', columnas: 4 },
    { clase: 'lg:col-span-4 lg:mt-16', columnas: 4 },
  ],
  // La fila de 3 y debajo su espejo (chica, mediana, grande).
  6: [
    ...FILA_PRINCIPAL,
    { clase: 'lg:col-span-3 lg:mt-12', columnas: 3 },
    { clase: 'lg:col-span-4 lg:mt-4', columnas: 4 },
    { clase: 'lg:col-span-5 lg:mt-14', columnas: 5 },
  ],
  // La fila de 3 y debajo cuatro desfasadas.
  7: [
    ...FILA_PRINCIPAL,
    { clase: 'lg:col-span-3 lg:mt-6', columnas: 3 },
    { clase: 'lg:col-span-3 lg:mt-16', columnas: 3 },
    { clase: 'lg:col-span-3 lg:mt-2', columnas: 3 },
    { clase: 'lg:col-span-3 lg:mt-12', columnas: 3 },
  ],
};

const MAX_FOTOS = 7;

/** Hasta 3 fotos en móvil: una columna alternando lados. */
const MOVIL_COLUMNA = [
  'w-[88%] self-start',
  'w-[72%] self-end mt-6',
  'w-[64%] self-start mt-6',
];

/**
 * Más de 3 fotos en móvil: la primera grande arriba y el resto en dos columnas,
 * con la de la derecha más abajo. Si queda una sola al final, va centrada.
 */
function movilDosColumnas(i: number, total: number): string {
  if (i === 0) return 'col-span-2 w-[88%] justify-self-start';
  const ultimaSola = i === total - 1 && (total - 1) % 2 === 1;
  if (ultimaSola) return 'col-span-2 w-[64%] justify-self-center mt-2';
  return i % 2 === 0 ? 'w-full mt-10' : 'w-full';
}

/** `sizes` para `next/image`, según lo que mide la foto en cada pantalla. */
function sizesPara(i: number, total: number, columnas: number): string {
  const movil = total <= 3 || i === 0 ? 88 : 46;
  // El contenido no pasa de 90rem (1440 px); arriba de eso la foto no crece.
  const escritorio = Math.round((columnas / 12) * 100);
  const tope = Math.round((columnas / 12) * 1440);
  return `(max-width: 1023px) ${movil}vw, (min-width: 1440px) ${tope}px, ${escritorio}vw`;
}

/**
 * Medidas para `next/image`. Con `h-auto` mandan solo como proporción, así que
 * cuando el backend no las pudo leer un 4:5 es mejor default que romper.
 */
const MEDIDAS_FALLBACK = { width: 1200, height: 1500 };

interface HeroMosaicProps {
  images: HeroImage[];
}

export function HeroMosaic({ images }: HeroMosaicProps) {
  const fotos = images.slice(0, MAX_FOTOS);
  if (fotos.length === 0) return null;

  const total = fotos.length;
  const escritorio = ESCRITORIO[total];
  const contenedor =
    total <= 3 ? 'flex flex-col' : 'grid grid-cols-2 items-start gap-x-4 gap-y-6';

  return (
    <div
      className={`${contenedor} lg:grid lg:grid-cols-12 lg:items-start lg:gap-x-6 lg:gap-y-10`}
    >
      {fotos.map((image, i) => {
        const movil = total <= 3 ? MOVIL_COLUMNA[i] : movilDosColumnas(i, total);
        const { clase, columnas } = escritorio[i];
        const width = image.width ?? MEDIDAS_FALLBACK.width;
        const height = image.height ?? MEDIDAS_FALLBACK.height;
        return (
          <figure
            key={image.id}
            className={`relative ${movil} ${clase} lg:w-full lg:justify-self-auto lg:self-auto`}
          >
            <div className="overflow-hidden rounded-2xl bg-piedra-100 shadow-lg ring-1 ring-piedra-200">
              <Image
                src={mediaUrl(image.image)}
                alt={image.alt_text}
                width={width}
                height={height}
                // La primera foto es casi siempre el LCP de la portada.
                priority={i === 0}
                sizes={sizesPara(i, total, columnas)}
                className="h-auto w-full"
              />
            </div>
            {image.caption && (
              <figcaption className="mt-2 px-1 font-manuscrita text-lg text-piedra-700">
                {image.caption}
              </figcaption>
            )}
          </figure>
        );
      })}
    </div>
  );
}

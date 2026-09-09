import Image from 'next/image';
import { mediaUrl } from '@/lib/media';
import type { HeroImage } from '@/types/homepage';

/**
 * Mosaico escalonado de la portada (hasta 3 fotos).
 *
 * No es una grilla pareja a propósito: cada foto tiene su propio ancho y su
 * desfase vertical, así que el conjunto se lee como una composición y no como
 * un carrete. En móvil se alternan a izquierda y derecha con anchos distintos,
 * que es el mismo escalonado en vertical; no se solapan porque el solape tapaba
 * el pie de foto de la anterior.
 *
 * Cada foto se muestra ENTERA, con la proporción que trae. Antes cada posición
 * imponía la suya (4/5, 1/1, 3/4) y `object-cover` recortaba lo que sobraba:
 * las fotos verticales del taller quedaban decapitadas. El escalonado ya lo dan
 * los anchos y los desfases; forzar la proporción solo costaba encuadre.
 *
 * `LAYOUT` está indexado por posición, no por foto: con una o dos fotos se usan
 * las primeras entradas y la composición sigue cerrando.
 */
const LAYOUT = [
  {
    // Móvil: casi todo el ancho, alineada a la izquierda.
    movil: 'w-[88%] self-start',
    // Escritorio: la más grande, arriba del todo.
    escritorio: 'lg:col-span-5 lg:mt-0 lg:w-full',
  },
  {
    movil: 'w-[72%] self-end mt-6',
    escritorio: 'lg:col-span-4 lg:mt-20 lg:w-full',
  },
  {
    movil: 'w-[64%] self-start mt-6',
    escritorio: 'lg:col-span-3 lg:mt-8 lg:w-full',
  },
];

/**
 * Medidas para `next/image`. Con `h-auto` mandan solo como proporción, así que
 * cuando el backend no las pudo leer un 4:5 es mejor default que romper.
 */
const MEDIDAS_FALLBACK = { width: 1200, height: 1500 };

interface HeroMosaicProps {
  images: HeroImage[];
}

export function HeroMosaic({ images }: HeroMosaicProps) {
  if (images.length === 0) return null;

  return (
    <div className="flex flex-col lg:grid lg:grid-cols-12 lg:items-start lg:gap-6">
      {images.slice(0, LAYOUT.length).map((image, i) => {
        const { movil, escritorio } = LAYOUT[i];
        const width = image.width ?? MEDIDAS_FALLBACK.width;
        const height = image.height ?? MEDIDAS_FALLBACK.height;
        return (
          <figure key={image.id} className={`relative ${movil} ${escritorio}`}>
            <div className="overflow-hidden rounded-2xl bg-piedra-100 shadow-lg ring-1 ring-piedra-200">
              <Image
                src={mediaUrl(image.image)}
                alt={image.alt_text}
                width={width}
                height={height}
                // La primera foto es casi siempre el LCP de la portada.
                priority={i === 0}
                sizes="(max-width: 1024px) 88vw, 40vw"
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

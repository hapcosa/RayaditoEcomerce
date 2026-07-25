'use client';

import Image from 'next/image';
import { useState } from 'react';
import type { GalleryImage } from '@/types/product';

interface ProductGalleryProps {
  mainPhoto: string;
  productName: string;
  gallery: GalleryImage[];
}

export function ProductGallery({
  mainPhoto,
  productName,
  gallery,
}: ProductGalleryProps) {
  const images = [
    ...(mainPhoto ? [mainPhoto] : []),
    ...gallery.map((g) => g.photo),
  ];
  const [active, setActive] = useState(0);

  if (images.length === 0) {
    return (
      <div className="flex aspect-square items-center justify-center rounded-2xl bg-piedra-100">
        <span className="font-manuscrita text-6xl text-piedra-300">✦</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="relative aspect-square overflow-hidden rounded-2xl bg-piedra-100">
        <Image
          src={images[active]}
          alt={`${productName} — imagen ${active + 1}`}
          fill
          sizes="(max-width: 768px) 100vw, 50vw"
          className="object-cover"
          priority={active === 0}
        />
      </div>

      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {images.map((src, i) => (
            <button
              key={src}
              onClick={() => setActive(i)}
              className={[
                'relative h-16 w-16 flex-shrink-0 overflow-hidden rounded-lg border-2 transition-colors',
                i === active
                  ? 'border-tierra-500'
                  : 'border-transparent hover:border-piedra-300',
              ].join(' ')}
              aria-label={`Ver imagen ${i + 1}`}
            >
              <Image src={src} alt="" fill sizes="64px" className="object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

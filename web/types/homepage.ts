/** Tipos de la portada. Espeja `homepage/serializers.py`. */

export interface HeroImage {
  id: number;
  image: string;
  alt_text: string;
  caption: string;
  position: number;
  /** Medidas reales del archivo. `null` si el archivo no se pudo leer. */
  width: number | null;
  height: number | null;
}

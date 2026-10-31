"""Achica las fotos que sube la dueña antes de guardarlas.

La app sube a calidad completa: una foto de celular moderno pesa ~10 MB y mide
hasta ~9000 px. `next/image` descarga ese original por el túnel para generar
cada tamaño y se rinde a los pocos segundos; en el celular (que pide anchos
grandes por la densidad de pantalla) la foto quedaba en blanco con el ícono de
imagen rota. Ninguna pantalla necesita más de `MAX_SIDE` px.
"""
import io
import os

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

# Lado mayor. Cubre un mosaico a pantalla completa en un monitor 2x.
MAX_SIDE = 2560
# Una foto ya chica pero muy pesada (calidad 100) también se recomprime.
MAX_BYTES = 2 * 1024 * 1024
JPEG_QUALITY = 85

# Formato de salida según el de entrada. MPO es el JPEG "multifoto" de algunos
# celulares; cualquier otro (HEIC, BMP...) se guarda como JPEG.
_KEEP = {'JPEG': 'JPEG', 'MPO': 'JPEG', 'PNG': 'PNG', 'WEBP': 'WEBP'}
_EXT = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp'}


def shrink(handle, size_bytes):
    """Bytes de la foto achicada y su formato, o `None` si ya está bien.

    Endereza según el EXIF: al reescribir el archivo se pierde la etiqueta de
    orientación, y sin esto la foto quedaría acostada.
    """
    image = Image.open(handle)
    source_format = image.format
    if max(image.size) <= MAX_SIDE and size_bytes <= MAX_BYTES:
        return None

    out_format = _KEEP.get(source_format, 'JPEG')
    if out_format == 'JPEG':
        # Decodifica directo a un tamaño cercano: no arma 38 MP en memoria.
        image.draft('RGB', (MAX_SIDE, MAX_SIDE))
    image = ImageOps.exif_transpose(image)
    image.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)

    buffer = io.BytesIO()
    if out_format == 'JPEG':
        image.convert('RGB').save(
            buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True,
        )
    else:
        image.save(buffer, format=out_format, optimize=True)
    return buffer.getvalue(), out_format


def shrink_upload(field_file):
    """Achica una foto recién subida, antes de que el modelo la guarde.

    Solo actúa sobre archivos sin guardar (`_committed` falso): editar el nombre
    de un producto no vuelve a procesar su foto.
    """
    if not field_file or field_file._committed:
        return
    upload = field_file.file
    upload.seek(0)
    result = shrink(upload, upload.size)
    upload.seek(0)
    if result is None:
        return
    data, out_format = result
    stem = os.path.splitext(os.path.basename(field_file.name))[0]
    field_file.save(f'{stem}{_EXT[out_format]}', ContentFile(data), save=False)


def shrink_stored(field_file, dry_run=False):
    """Achica una foto ya guardada, en el mismo lugar. True si la cambió.

    Mantiene el nombre (y por lo tanto la URL): el formato de salida sigue al
    de entrada, así un `.jpg` sigue siendo JPEG.
    """
    storage = field_file.storage
    name = field_file.name
    if not name or not storage.exists(name):
        return False
    with storage.open(name, 'rb') as handle:
        result = shrink(handle, storage.size(name))
    if result is None:
        return False
    if not dry_run:
        storage.delete(name)
        saved = storage.save(name, ContentFile(result[0]))
        if saved != name:  # el storage no reusó el nombre: apuntar al nuevo
            field_file.name = saved
            field_file.instance.save(update_fields=[field_file.field.name])
    return True

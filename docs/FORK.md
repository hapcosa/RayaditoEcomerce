# Cómo crear un fork (otra tienda sobre este repo)

Este repo es la base de varias tiendas: **Piedras Rayadito** (joyería) es la
primera, y cada rubro nuevo (por ejemplo ropa tejida) es un **fork por git** que
cambia configuración, marca y contenido, **no código**.

La regla que hace que esto funcione: **el fork solo edita los archivos propios
de la tienda** (lista abajo). Todo lo demás es código común; si una tienda
necesita algo nuevo, se hace primero acá (upstream) con su PR y el fork lo trae
con un `git merge`. Así los arreglos de seguridad y las mejoras llegan a todas
las tiendas sin conflictos.

> No uses la función "template repository" de GitHub: crea un repo **sin
> historia**, y sin historia común `git merge upstream/master` no funciona.

## 1. Crear el repo del fork

```bash
# En GitHub: crear un repo vacío y privado (sin README), ej. hapcosa/colilargaecommerce.
git clone https://github.com/hapcosa/RayaditoEcomerce.git colilargaecommerce
cd colilargaecommerce
git remote rename origin upstream          # Rayadito queda como "upstream"
git remote add origin https://github.com/hapcosa/colilargaecommerce.git
git push -u origin master
```

En el repo nuevo: activar los mismos checks de CI como requeridos para
`master` (Settings → Branches) y "Automatically delete head branches".

## 2. Archivos propios de la tienda

| Archivo | Qué cambia |
|---|---|
| `store.json` | Nombre, slug, dominio, rubro, textos de marca y correos, **catálogos** (`catalogs`), sección `web` (título, descripción, ubicación, logo, contacto). Lo leen Django, la tienda y la app admin. |
| `web/app/theme.css` | Paleta de colores (variables CSS). |
| `web/content/*` | Textos largos: portada, nosotros, FAQ, intro de términos. |
| `web/public/<logo>.png` | Logo del header (ruta y tamaño en `store.json` → `web.logo*`). |
| `web/app/icon.png`, `apple-icon.png`, `opengraph-image.png` | Favicon e imagen para compartir. |
| `web/app/productos/[slug]/opengraph-image.tsx` | Solo las 5 constantes de color del inicio (copia de `theme.css`: el generador de imágenes no lee variables CSS). |
| `admin-app/app.json` | Identidad nativa del APK: `name`, `slug`, `scheme`, `android.package`, colores de splash/ícono. |
| `admin-app/assets/images/*` | Íconos, splash y `brand-logo-ondark.png` (logo del login). |
| `admin-app/src/constants/theme.ts` | Colores de la app admin. |
| `.env`, `web/.env.local`, `admin-app/.env` | Secretos y URLs (no van a git; ver los `.example`). |

Opcional: la primera línea de `README.md` y `AGENTS.md` (descripción de la
tienda).

### `store.json`: los catálogos

Cada catálogo es una vitrina pública:

```jsonc
{
  "slug": "ropa",          // valor de Product.product_type
  "path": "ropa",          // URL: /ropa
  "label": "Ropa",         // menú y título
  "singular": "Prenda",    // chips de la app admin
  "category_type": "Ropa", // Category.ProductType de sus categorías
  "description": "Prendas tejidas a mano…",
  "item_label": "Prenda tejida" // rótulo en la imagen para compartir
}
```

El primer catálogo es el principal ("Ver todo", botones de la portada). Django
valida el archivo al arrancar y dice qué falta si algo está mal.

## 3. Base de datos y datos demo

Cada tienda tiene **su propia base**. En el `.env` del fork:

```bash
DB_NAME=colilarga
DB_USER=colilarga
DB_PASSWORD=<otra-contraseña>
DB_PORT=15433          # si convive con Rayadito en la misma máquina
```

```bash
docker compose -p colilarga up -d db     # -p: proyecto aparte, volumen aparte
python manage.py migrate
python manage.py seed_demo               # usa el "rubro" de store.json
python manage.py createsuperuser
```

`seed_demo` trae datos por rubro (`product/seeds.py`): `joyeria` y `textil`.
Para un rubro nuevo, agregar su set en ese archivo **upstream** (es código
común).

## 4. Deploy

Sigue [`DEPLOY.md`](DEPLOY.md) con estas diferencias si comparte servidor con
otra tienda:

- **Checkout aparte** y **puertos aparte** para Django y Next.js.
- **Servicios systemd con el slug** de la tienda (`colilarga-api`,
  `colilarga-web`, `colilarga-tunnel`). `scripts/install-prod-timers.sh` ya
  toma el prefijo de `store.json` (`colilarga-backup.timer`, …).
- **Túnel de Cloudflare propio** (`~/.cloudflared-colilarga/`) con el dominio
  de la tienda.
- `scripts/pull-prod-backups.sh`: definir `PROD_HOST`, `REMOTE_DIR` y `DEST`.

## 5. Traer mejoras de upstream

```bash
git fetch upstream
git switch -c chore/merge-upstream
git merge upstream/master
# conflictos: solo deberían aparecer en archivos propios de la tienda
python manage.py migrate && python manage.py test
git push -u origin chore/merge-upstream    # PR en el repo del fork
```

Si `store.json` choca, casi siempre es porque upstream agregó una clave nueva:
conservar los valores del fork y sumar la clave.

## 6. Qué NO hacer en el fork

- Editar componentes, vistas, modelos o tests para "adaptarlos": eso hace
  divergir el fork. Si hace falta, hacerlo **configurable upstream**.
- Escribir la marca o los catálogos directo en el código (en ningún repo).
- Reutilizar la base, el bucket de fotos o las credenciales de otra tienda.

## Limitación conocida

Las **variantes comprables** (ej. una prenda en tallas S/M/L, cada una con su
stock) existen en el modelo (`ProductVariant`) pero el carrito y los pedidos
todavía compran el producto, no la variante. Para piezas únicas (stock 1, la
talla como atributo) funciona hoy; tallas con stock propio requieren ese
desarrollo upstream (ROADMAP Fase 8).

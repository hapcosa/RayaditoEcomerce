"""Datos demo por rubro para `seed_demo`.

Cada rubro declara sus atributos, categorías y productos de ejemplo. El
catálogo de cada producto (`catalog`) y el rubro de cada categoría
(`category_type`) tienen que existir en el store.json de la tienda: el
comando lo verifica antes de escribir nada.

Valores de atributos: slug -> (texto es-CL, valor numérico o None).
"""
from decimal import Decimal

SHIPPING = [
    {
        "name": "Starken - Por pagar",
        "time_to_delivery": "2 a 5 días hábiles",
        "description": "Envío a sucursal Starken, pago en destino.",
    },
    {
        "name": "Retiro en taller",
        "time_to_delivery": "Coordinar",
        "description": "Retiro en el taller.",
    },
]

JOYERIA = {
    # Sembrados por product.0009; se crean solo si faltan.
    "attributes": [
        {"slug": "material", "name": "Material", "kind": "select"},
        {"slug": "peso", "name": "Peso", "kind": "decimal", "unit": "g"},
        {"slug": "nombre-piedra", "name": "Piedra", "kind": "select"},
        {"slug": "dureza-mohs", "name": "Dureza (Mohs)", "kind": "decimal"},
        {"slug": "origen", "name": "Origen", "kind": "select"},
        {"slug": "largo", "name": "Largo", "kind": "decimal", "unit": "cm"},
        {"slug": "ancho", "name": "Ancho", "kind": "decimal", "unit": "cm"},
        {"slug": "alto", "name": "Alto", "kind": "decimal", "unit": "cm"},
    ],
    # Los atributos se declaran en la raíz y las hijas los heredan.
    "categories": [
        {"name": "Joyas", "category_type": "Joya", "attributes": ["material", "peso"]},
        {"name": "Anillos", "category_type": "Joya", "parent": "Joyas"},
        {
            "name": "Piedras",
            "category_type": "Piedra",
            "attributes": ["nombre-piedra", "dureza-mohs", "origen", "largo", "ancho", "alto"],
        },
        {"name": "Ágatas", "category_type": "Piedra", "parent": "Piedras"},
    ],
    "products": [
        {
            "name": "Anillo de plata con ágata",
            "catalog": "joya",
            "category": "Anillos",
            "price": 25000,
            "description": "Anillo artesanal de plata 950 con ágata de Chiloé.",
            "attributes": {
                "material": ("Plata 950", None),
                "peso": ("12,5", Decimal("12.5")),
            },
        },
        {
            "name": "Ágata lapidada",
            "catalog": "piedra",
            "category": "Ágatas",
            "price": 12000,
            "description": "Ágata local lapidada a mano.",
            "attributes": {
                "nombre-piedra": ("Ágata de Chiloé", None),
                "dureza-mohs": ("7", Decimal("7")),
                "origen": ("Volcanico", None),
                "largo": ("3,5", Decimal("3.5")),
                "ancho": ("2", Decimal("2")),
                "alto": ("1,2", Decimal("1.2")),
            },
        },
    ],
}

# Ropa confeccionada a mano: piezas únicas, con la talla como dato de la
# prenda. (Las tallas como variantes comprables con stock propio necesitan
# soporte de variantes en carrito y pedidos; ver ROADMAP Fase 8.)
TEXTIL = {
    "attributes": [
        {"slug": "talla", "name": "Talla", "kind": "select"},
        {"slug": "color", "name": "Color", "kind": "select"},
        {"slug": "material", "name": "Material", "kind": "select"},
        {"slug": "largo", "name": "Largo", "kind": "decimal", "unit": "cm"},
        {"slug": "ancho", "name": "Ancho", "kind": "decimal", "unit": "cm"},
    ],
    "categories": [
        {
            "name": "Ropa",
            "category_type": "Ropa",
            "attributes": ["talla", "color", "material", "largo", "ancho"],
        },
        {"name": "Chalecos", "category_type": "Ropa", "parent": "Ropa"},
        {"name": "Gorros", "category_type": "Ropa", "parent": "Ropa"},
    ],
    "products": [
        {
            "name": "Chaleco de lana de oveja",
            "catalog": "ropa",
            "category": "Chalecos",
            "price": 45000,
            "description": "Chaleco tejido a palillo con lana de oveja hilada a mano.",
            "attributes": {
                "talla": ("M", None),
                "color": ("Gris natural", None),
                "material": ("Lana de oveja", None),
                "largo": ("68", Decimal("68")),
                "ancho": ("52", Decimal("52")),
            },
        },
        {
            "name": "Gorro tejido",
            "catalog": "ropa",
            "category": "Gorros",
            "price": 15000,
            "description": "Gorro tejido a crochet, forrado por dentro.",
            "attributes": {
                "talla": ("Única", None),
                "color": ("Burdeo", None),
                "material": ("Lana de oveja", None),
            },
        },
    ],
}

SEEDS = {"joyeria": JOYERIA, "textil": TEXTIL}

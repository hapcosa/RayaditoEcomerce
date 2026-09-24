"""Lo que quedo despues de desarmar las subclases `Joyas`/`Piedras`.

La migracion de datos en si (0012) no se prueba con el `MigrationExecutor`:
0013 borra los modelos y no es reversible, asi que volver al estado anterior
dentro de un test falla al recrear las tablas. Lo que si se cubre es la
funcion de formato —donde estaba el riesgo real de ensuciar los datos— y que
el modelo quedo limpio. La migracion sobre datos reales se corrio a mano
contra la base de desarrollo antes del merge; el resultado esta en el PR.
"""
from decimal import Decimal
from importlib import import_module

from django.apps import apps
from django.test import SimpleTestCase

# El modulo empieza con digito, asi que no se puede importar con `from ... import`.
texto_es_cl = import_module('product.migrations.0012_subclasses_to_attributes').texto_es_cl


class TextoEsClTests(SimpleTestCase):
    """El valor guardado se lee como lo escribiria el staff en es-CL."""

    def test_saca_los_ceros_de_relleno(self):
        self.assertEqual(texto_es_cl(Decimal('12.50')), '12,5')
        self.assertEqual(texto_es_cl(Decimal('3.00')), '3')
        self.assertEqual(texto_es_cl(Decimal('0.50')), '0,5')

    def test_no_deja_notacion_cientifica(self):
        """normalize() convierte 20 en 2E+1; el formato 'f' lo devuelve a 20."""
        self.assertEqual(texto_es_cl(Decimal('20.00')), '20')
        self.assertEqual(texto_es_cl(Decimal('100.000')), '100')


class ModeloSinSubclasesTests(SimpleTestCase):
    def test_los_modelos_ya_no_existen(self):
        for nombre in ('Joyas', 'Piedras', 'RelationPiedraJoya', 'JoyaMateriales'):
            with self.subTest(modelo=nombre):
                with self.assertRaises(LookupError):
                    apps.get_model('product', nombre)

    def test_product_sigue_entero(self):
        Product = apps.get_model('product', 'Product')
        campos = {f.name for f in Product._meta.get_fields()}
        self.assertIn('attribute_values', campos)
        self.assertIn('product_type', campos)

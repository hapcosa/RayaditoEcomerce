"""Tests de la API staff de atributos y su enganche a categorías.

Cubre lo que la app admin necesita para que el dueño defina, desde el teléfono,
una enumeración nueva ("Métrica europea" con sus tallas) y la aplique a una
categoría, más las medidas libres de las piedras (alto/ancho/largo).
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from category.models import Category, CategoryAttribute
from product.models import (
    Attribute, AttributeKind, AttributeValue, Product, ProductAttributeValue,
    ProductVariant, ProductVariantAttributeValue,
)

User = get_user_model()


class AdminAttributeApiTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email='dueno@rayadito.cl', password='Testpass123',
            first_name='Due', last_name='Ño', is_staff=True,
        )
        self.cliente = User.objects.create_user(
            email='cliente@rayadito.cl', password='Testpass123',
            first_name='Cli', last_name='Ente',
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    # --- permisos ---------------------------------------------------------

    def test_anonymous_cannot_list_attributes(self):
        response = self.client.get('/api/admin/attributes/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_staff_cannot_create_attribute(self):
        self._auth(self.cliente)
        response = self.client.post(
            '/api/admin/attributes/', {'name': 'Talla', 'kind': 'select'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- alta de enumeraciones -------------------------------------------

    def test_staff_creates_select_attribute_and_slug_is_derived(self):
        self._auth(self.staff)
        response = self.client.post('/api/admin/attributes/', {
            'name': 'Métrica europea', 'kind': 'select', 'is_variant_option': True,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['slug'], 'metrica-europea')
        self.assertTrue(response.data['is_variant_option'])

    def test_duplicate_name_gets_a_distinct_slug(self):
        self._auth(self.staff)
        first = self.client.post('/api/admin/attributes/', {'name': 'Talla'})
        second = self.client.post('/api/admin/attributes/', {'name': 'Talla'})
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(first.data['slug'], second.data['slug'])

    def test_blank_name_is_rejected(self):
        self._auth(self.staff)
        response = self.client.post('/api/admin/attributes/', {'name': '   '})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_numeric_attribute_cannot_be_a_variant_option(self):
        """Un alto en cm no define stock comprable; solo una selección lo hace."""
        self._auth(self.staff)
        response = self.client.post('/api/admin/attributes/', {
            'name': 'Alto', 'kind': 'decimal', 'unit': 'cm',
            'is_variant_option': True,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is_variant_option', response.data)

    def test_stone_measurements_are_already_seeded(self):
        """Alto/Ancho/Largo vienen de la migración 0009, en cm y no variantes."""
        self._auth(self.staff)
        response = self.client.get('/api/admin/attributes/')
        por_slug = {row['slug']: row for row in response.data}
        for slug in ('alto', 'ancho', 'largo'):
            self.assertIn(slug, por_slug)
            self.assertEqual(por_slug[slug]['unit'], 'cm')
            self.assertEqual(por_slug[slug]['kind'], 'decimal')
            self.assertFalse(por_slug[slug]['is_variant_option'])

    # --- valores de la enumeración ---------------------------------------

    def test_staff_adds_values_to_select_attribute(self):
        self._auth(self.staff)
        attribute = Attribute.objects.create(
            name='Métrica europea', slug='metrica-europea', kind=AttributeKind.SELECT,
            is_variant_option=True,
        )
        for i, talla in enumerate(['16', '17', '18']):
            response = self.client.post(
                f'/api/admin/attributes/{attribute.id}/values/',
                {'value': talla, 'numeric_value': talla, 'sort_order': i},
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(attribute.values.count(), 3)

    def test_duplicate_value_in_same_attribute_is_409(self):
        self._auth(self.staff)
        attribute = Attribute.objects.create(
            name='Talla', slug='talla', kind=AttributeKind.SELECT,
        )
        AttributeValue.objects.create(attribute=attribute, value='M')
        response = self.client.post(
            f'/api/admin/attributes/{attribute.id}/values/', {'value': 'M'},
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_cannot_add_values_to_a_numeric_attribute(self):
        self._auth(self.staff)
        attribute = Attribute.objects.get(slug='alto')
        response = self.client.post(
            f'/api/admin/attributes/{attribute.id}/values/', {'value': '3.5'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_edits_and_deletes_a_value(self):
        self._auth(self.staff)
        attribute = Attribute.objects.create(
            name='Talla', slug='talla', kind=AttributeKind.SELECT,
        )
        value = AttributeValue.objects.create(attribute=attribute, value='M')
        edited = self.client.patch(
            f'/api/admin/attributes/{attribute.id}/values/{value.id}/',
            {'value': 'L'},
        )
        self.assertEqual(edited.status_code, status.HTTP_200_OK)
        self.assertEqual(edited.data['value'], 'L')
        deleted = self.client.delete(
            f'/api/admin/attributes/{attribute.id}/values/{value.id}/',
        )
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AttributeValue.objects.filter(id=value.id).exists())

    def test_value_of_another_attribute_is_404(self):
        self._auth(self.staff)
        talla = Attribute.objects.create(
            name='Talla', slug='talla', kind=AttributeKind.SELECT,
        )
        color = Attribute.objects.create(
            name='Color', slug='color', kind=AttributeKind.SELECT,
        )
        ajeno = AttributeValue.objects.create(attribute=color, value='Verde')
        response = self.client.delete(
            f'/api/admin/attributes/{talla.id}/values/{ajeno.id}/',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- borrado protegido ------------------------------------------------

    def _producto(self, categoria=None):
        categoria = categoria or Category.objects.create(
            name='Anillos', ProductType='Joya',
        )
        return Product.objects.create(
            name='Anillo de prueba', description='x', price=20000,
            category=categoria, photo='photos/x.png',
        )

    def test_cannot_delete_attribute_in_use_by_a_product(self):
        self._auth(self.staff)
        attribute = Attribute.objects.create(
            name='Talla', slug='talla', kind=AttributeKind.SELECT,
        )
        value = AttributeValue.objects.create(attribute=attribute, value='M')
        ProductAttributeValue.objects.create(
            product=self._producto(), attribute_value=value,
        )
        response = self.client.delete(f'/api/admin/attributes/{attribute.id}/')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Attribute.objects.filter(id=attribute.id).exists())

    def test_cannot_delete_value_in_use_by_a_variant(self):
        self._auth(self.staff)
        attribute = Attribute.objects.create(
            name='Talla', slug='talla', kind=AttributeKind.SELECT,
            is_variant_option=True,
        )
        value = AttributeValue.objects.create(attribute=attribute, value='M')
        variant = ProductVariant.objects.create(product=self._producto(), stock=3)
        ProductVariantAttributeValue.objects.create(
            variant=variant, attribute_value=value,
        )
        response = self.client.delete(
            f'/api/admin/attributes/{attribute.id}/values/{value.id}/',
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_unused_attribute_can_be_deleted(self):
        self._auth(self.staff)
        attribute = Attribute.objects.create(
            name='Talla', slug='talla', kind=AttributeKind.SELECT,
        )
        response = self.client.delete(f'/api/admin/attributes/{attribute.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class AdminCategoryAttributeApiTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email='dueno@rayadito.cl', password='Testpass123',
            first_name='Due', last_name='Ño', is_staff=True,
        )
        self.client.force_authenticate(user=self.staff)
        self.joyas = Category.objects.create(name='Joyas', ProductType='Joya')
        self.anillos = Category.objects.create(
            name='Anillos', ProductType='Joya', parent=self.joyas,
        )
        self.talla = Attribute.objects.create(
            name='Talla', slug='talla', kind=AttributeKind.SELECT,
            is_variant_option=True,
        )
        # Sembrado por la migración 0009 (ver seed_generic_product_data).
        self.material = Attribute.objects.get(slug='material')

    def test_staff_attaches_attribute_to_category(self):
        response = self.client.post(
            f'/api/admin/categories/{self.anillos.id}/attributes/',
            {'attribute_id': self.talla.id, 'is_required': True},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_required'])
        self.assertEqual(response.data['attribute']['name'], 'Talla')
        self.assertIsNone(response.data['inherited_from'])

    def test_attaching_twice_is_409(self):
        CategoryAttribute.objects.create(
            category=self.anillos, attribute=self.talla,
        )
        response = self.client.post(
            f'/api/admin/categories/{self.anillos.id}/attributes/',
            {'attribute_id': self.talla.id},
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_child_category_inherits_parent_attributes(self):
        CategoryAttribute.objects.create(
            category=self.joyas, attribute=self.material,
        )
        CategoryAttribute.objects.create(
            category=self.anillos, attribute=self.talla,
        )
        response = self.client.get(
            f'/api/admin/categories/{self.anillos.id}/attributes/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        por_nombre = {row['attribute']['name']: row for row in response.data}
        self.assertEqual(set(por_nombre), {'Talla', 'Material'})
        self.assertIsNone(por_nombre['Talla']['inherited_from'])
        self.assertEqual(por_nombre['Material']['inherited_from']['name'], 'Joyas')

    def test_own_link_overrides_inherited_one(self):
        """La hija puede aflojar lo que la madre marcó obligatorio."""
        CategoryAttribute.objects.create(
            category=self.joyas, attribute=self.material, is_required=True,
        )
        CategoryAttribute.objects.create(
            category=self.anillos, attribute=self.material, is_required=False,
        )
        response = self.client.get(
            f'/api/admin/categories/{self.anillos.id}/attributes/',
        )
        filas = [r for r in response.data if r['attribute']['name'] == 'Material']
        self.assertEqual(len(filas), 1)
        self.assertFalse(filas[0]['is_required'])
        self.assertIsNone(filas[0]['inherited_from'])

    def test_parent_does_not_see_child_attributes(self):
        CategoryAttribute.objects.create(
            category=self.anillos, attribute=self.talla,
        )
        response = self.client.get(
            f'/api/admin/categories/{self.joyas.id}/attributes/',
        )
        self.assertEqual(response.data, [])

    def test_staff_updates_and_detaches_own_link(self):
        CategoryAttribute.objects.create(
            category=self.anillos, attribute=self.talla, is_required=False,
        )
        edited = self.client.patch(
            f'/api/admin/categories/{self.anillos.id}/attributes/{self.talla.id}/',
            {'is_required': True},
        )
        self.assertEqual(edited.status_code, status.HTTP_200_OK)
        self.assertTrue(edited.data['is_required'])
        deleted = self.client.delete(
            f'/api/admin/categories/{self.anillos.id}/attributes/{self.talla.id}/',
        )
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CategoryAttribute.objects.filter(
            category=self.anillos, attribute=self.talla,
        ).exists())

    def test_cannot_detach_inherited_attribute_from_child(self):
        CategoryAttribute.objects.create(
            category=self.joyas, attribute=self.material,
        )
        response = self.client.delete(
            f'/api/admin/categories/{self.anillos.id}/attributes/{self.material.id}/',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('madre', response.data['detail'])
        self.assertTrue(CategoryAttribute.objects.filter(
            category=self.joyas, attribute=self.material,
        ).exists())

    def test_stone_category_gets_free_measurements(self):
        """El caso de piedras: alto/ancho/largo en cm, sin enumeración."""
        piedras = Category.objects.create(name='Piedras', ProductType='Piedra')
        for slug in ('alto', 'ancho', 'largo'):
            attr = Attribute.objects.get(slug=slug)
            response = self.client.post(
                f'/api/admin/categories/{piedras.id}/attributes/',
                {'attribute_id': attr.id, 'is_required': True},
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        listado = self.client.get(f'/api/admin/categories/{piedras.id}/attributes/')
        self.assertEqual(len(listado.data), 3)
        self.assertTrue(all(r['attribute']['unit'] == 'cm' for r in listado.data))
        self.assertTrue(all(
            not r['attribute']['is_variant_option'] for r in listado.data
        ))

    def test_cycle_in_category_tree_does_not_hang(self):
        """El árbol no impide ciclos a nivel de BD; recorrerlo no debe colgarse."""
        self.joyas.parent = self.anillos
        self.joyas.save()
        CategoryAttribute.objects.create(
            category=self.anillos, attribute=self.talla,
        )
        response = self.client.get(
            f'/api/admin/categories/{self.anillos.id}/attributes/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminProductAttributeValueApiTests(APITestCase):
    """Ficha de atributos de un producto: `/api/admin/products/{id}/attributes/`.

    El caso del dueño: cada anillo es una pieza única y lleva SU talla, así que
    el valor va en el producto y no genera variantes con stock propio.
    """

    def setUp(self):
        self.staff = User.objects.create_user(
            email='dueno@rayadito.cl', password='Testpass123',
            first_name='Due', last_name='Ño', is_staff=True,
        )
        self.joyas = Category.objects.create(name='Joyas', ProductType='Joya')
        self.anillos = Category.objects.create(
            name='Anillos', ProductType='Joya', parent=self.joyas,
        )
        self.talla = Attribute.objects.create(
            name='Talla', slug='talla-test', kind=AttributeKind.SELECT,
        )
        self.t16 = AttributeValue.objects.create(attribute=self.talla, value='16')
        self.t17 = AttributeValue.objects.create(attribute=self.talla, value='17')
        self.alto = Attribute.objects.create(
            name='Alto', slug='alto-test', unit='cm', kind=AttributeKind.DECIMAL,
        )
        CategoryAttribute.objects.create(
            category=self.anillos, attribute=self.talla,
        )
        # Heredado: lo define la madre y también aplica al anillo.
        CategoryAttribute.objects.create(category=self.joyas, attribute=self.alto)
        self.producto = Product.objects.create(
            name='Anillo ágata', description='x', price=20000,
            category=self.anillos, photo='photos/x.png',
        )
        self.url = f'/api/admin/products/{self.producto.pk}/attributes/'
        self.client.force_authenticate(user=self.staff)

    def test_get_lists_own_and_inherited_attributes_without_values(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        porNombre = {row['attribute']['name']: row for row in response.data}
        self.assertEqual(set(porNombre), {'Talla', 'Alto'})
        self.assertIsNone(porNombre['Talla']['value'])
        self.assertIsNone(porNombre['Talla']['inherited_from'])
        self.assertEqual(porNombre['Alto']['inherited_from']['name'], 'Joyas')

    def test_put_assigns_a_select_value(self):
        response = self.client.put(self.url, {'values': [
            {'attribute_id': self.talla.pk, 'value_id': self.t16.pk},
        ]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        porNombre = {row['attribute']['name']: row for row in response.data}
        self.assertEqual(porNombre['Talla']['value'], '16')
        self.assertEqual(
            list(self.producto.attribute_values.values_list(
                'attribute_value__value', flat=True)),
            ['16'],
        )

    def test_reassigning_replaces_the_previous_value(self):
        self.client.put(self.url, {'values': [
            {'attribute_id': self.talla.pk, 'value_id': self.t16.pk},
        ]}, format='json')
        self.client.put(self.url, {'values': [
            {'attribute_id': self.talla.pk, 'value_id': self.t17.pk},
        ]}, format='json')
        self.assertEqual(
            list(self.producto.attribute_values.values_list(
                'attribute_value__value', flat=True)),
            ['17'],
        )

    def test_null_value_clears_it(self):
        self.client.put(self.url, {'values': [
            {'attribute_id': self.talla.pk, 'value_id': self.t16.pk},
        ]}, format='json')
        response = self.client.put(self.url, {'values': [
            {'attribute_id': self.talla.pk, 'value_id': None},
        ]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.producto.attribute_values.exists())

    def test_put_only_touches_the_attributes_it_names(self):
        self.client.put(self.url, {'values': [
            {'attribute_id': self.talla.pk, 'value_id': self.t16.pk},
        ]}, format='json')
        self.client.put(self.url, {'values': [
            {'attribute_id': self.alto.pk, 'value': '3,5'},
        ]}, format='json')
        valores = set(self.producto.attribute_values.values_list(
            'attribute_value__value', flat=True))
        self.assertEqual(valores, {'16', '3,5'})

    def test_free_value_creates_the_attribute_value_with_its_number(self):
        response = self.client.put(self.url, {'values': [
            {'attribute_id': self.alto.pk, 'value': '3,5'},
        ]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        creado = AttributeValue.objects.get(attribute=self.alto, value='3,5')
        self.assertEqual(str(creado.numeric_value), '3.500')

    def test_free_value_is_reused_not_duplicated(self):
        self.client.put(self.url, {'values': [
            {'attribute_id': self.alto.pk, 'value': '3,5'},
        ]}, format='json')
        otro = Product.objects.create(
            name='Otro anillo', description='x', price=1000,
            category=self.anillos, photo='photos/x.png',
        )
        self.client.put(f'/api/admin/products/{otro.pk}/attributes/', {'values': [
            {'attribute_id': self.alto.pk, 'value': '3,5'},
        ]}, format='json')
        self.assertEqual(
            AttributeValue.objects.filter(attribute=self.alto, value='3,5').count(), 1,
        )

    def test_decimal_attribute_rejects_text(self):
        response = self.client.put(self.url, {'values': [
            {'attribute_id': self.alto.pk, 'value': 'grande'},
        ]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('número', response.data['detail'])
        self.assertFalse(self.producto.attribute_values.exists())

    def test_integer_attribute_rejects_decimals(self):
        piezas = Attribute.objects.create(
            name='Piezas', slug='piezas-test', kind=AttributeKind.INTEGER,
        )
        CategoryAttribute.objects.create(category=self.anillos, attribute=piezas)
        response = self.client.put(self.url, {'values': [
            {'attribute_id': piezas.pk, 'value': '2,5'},
        ]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('entero', response.data['detail'])

    def test_attribute_not_hooked_to_the_category_is_rejected(self):
        suelto = Attribute.objects.create(
            name='Origen', slug='origen-test', kind=AttributeKind.TEXT,
        )
        response = self.client.put(self.url, {'values': [
            {'attribute_id': suelto.pk, 'value': 'Chiloé'},
        ]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no aplica', response.data['detail'])

    def test_value_from_another_attribute_is_rejected(self):
        otra = Attribute.objects.create(
            name='Color', slug='color-test', kind=AttributeKind.SELECT,
        )
        ajeno = AttributeValue.objects.create(attribute=otra, value='Verde')
        response = self.client.put(self.url, {'values': [
            {'attribute_id': self.talla.pk, 'value_id': ajeno.pk},
        ]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no pertenece', response.data['detail'])

    def test_nothing_is_written_when_one_entry_is_invalid(self):
        """Se valida todo antes de escribir: media ficha guardada es peor."""
        response = self.client.put(self.url, {'values': [
            {'attribute_id': self.talla.pk, 'value_id': self.t16.pk},
            {'attribute_id': self.alto.pk, 'value': 'grande'},
        ]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.producto.attribute_values.exists())

    def test_missing_values_key_is_rejected(self):
        response = self.client.put(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_staff_cannot_write_values(self):
        cliente = User.objects.create_user(
            email='cliente2@rayadito.cl', password='Testpass123',
            first_name='C', last_name='L',
        )
        self.client.force_authenticate(user=cliente)
        response = self.client.put(self.url, {'values': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

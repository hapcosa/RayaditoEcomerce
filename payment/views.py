from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework import permissions, status
from product.models import Product
from product.serializers import ProductSerializer
from carrito.models import Carrito,CarritoItem
from orders.models import *
from user_profile.models import UserProfile
from shipping.models import Shipping
User = settings.AUTH_USER_MODEL
import environ
import mercadopago
from mercadopago.resources import MerchantOrder
from .models import Payments
import os
import environ
import requests
import json
env = environ.Env()
environ.Env.read_env()

class ProcessPaymentView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        
        data=self.request.data
        user=self.request.user
        orderKey='orderId'
        print(data)
        if orderKey in data:
            try:
                print(orderKey)
                orderId=data[orderKey]
            except:
                return Response(
                        {'error': 'El dato identificador de la orden debe ser un numero entero'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            if Order.objects.filter(id=orderId).exists():
                order = Order.objects.get(id=orderId)
                shipping=Shipping.objects.get(id=order.shipping_id.id)
                total_amount = 0
                items = []
                email=user.email
                first_name = user.first_name
                last_name = user.last_name
                address_line_1 = order.address_line_1
                city=order.city
                state_province_region =order.region
                postal_zip_code =order.postal_zip_code
                telephone_number =order.telephone_number
                products = OrderItem.objects.filter(order=order)
                for product in products:
                    producto= Product.objects.get(id=product.product.id)
                    print(producto)
                    productos = {}
                    productos['id'] = producto.id
                    productos['title'] = producto.name
                    productos['currency_id'] = 'CLP'
                    productos['description'] = producto.description
                    productos['category_id'] = producto.category.id
                    productos['quantity'] = 1
                    productos['unit_price'] = float(producto.price)
                    total_amount += float(producto.price)
                    items.append(productos)
            else:
                return Response(
                        {'error': 'No existe la orden, vuelve a intentarlo'},
                        status=status.HTTP_404_NOT_FOUND
                    )
        
        else:
            print("---payment----")
            shipping_id = str(data['shipping_id'])
            shipping=Shipping.objects.get(id=shipping_id)
            total_amount = 0
            items = []
            if user.is_anonymous is False:
                profile_id = int(data['profile_id'])
                profile_address = UserProfile.objects.get(id=profile_id)
                email=user.email
                first_name = user.first_name
                last_name = user.last_name
                address_line_1 = profile_address.address_line_1
                city=profile_address.city
                state_province_region =profile_address.country_region
                postal_zip_code =profile_address.zipcode
                telephone_number =profile_address.phone
                cart = Carrito.objects.get(user=user)
                if not CarritoItem.objects.filter(carrito=cart).exists():
                    return Response(
                        {'error': 'No tienes productos en tu carrito'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                products = CarritoItem.objects.filter(carrito=cart)
                for product in products:
                    producto= Product.objects.get(id=product.product.id)
                    print(producto)
                    productos = {}
                    productos['id'] = producto.id
                    productos['title'] = producto.name
                    productos['currency_id'] = 'CLP'
                    productos['description'] = producto.description
                    productos['category_id'] = producto.category.id
                    productos['quantity'] = 1
                    productos['unit_price'] = float(producto.price)
                    total_amount += float(producto.price)
                    items.append(productos)
            else:

                    email=data['email']
                    first_name = data['first_name']
                    last_name = data['last_name']
                    address_line_1 = data['address_line_1']
                    city = data['city']
                    state_province_region = data['state_province_region']
                    postal_zip_code = data['postal_zip_code']
                    telephone_number = data['telephone_number']
                    products = data['items']
                    if products is None:
                        return Response(
                            {'error': 'No tienes productos en tu carrito'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    for num in range(0,len(products)):
                        productos = { }
                        
                        products_dict=products[num]
                        product=products_dict['product']
                        productos['id'] = product['id']
                        productos['title'] = str(product['name'])
                        productos['currency_id'] = 'CLP'
                        productos['description'] = str(product['description'])
                        productos['category_id'] = str(product['category'])
                        productos['quantity'] = 1
                        productos['unit_price'] = float(product['price'])
                        total_amount += float(product['price'])
                        items.append(productos)

            
                    
                
            print("crea la orden")
            order = Order.objects.create()
        preference_data = { 
            "items": items,
            "notification_url": "https://7f53-191-127-233-0.ngrok-free.app/api/payment/webhook",
            "back_urls": {
                "success": "http://127.0.0.1:5173/",
                "failure": "http://127.0.0.1:5173/",
                "pending": "http://127.0.0.1:5173/"
            },
            
            "auto_return": "approved",
            "installments": 3,
            "external_Reference": order.id,
            "expires": True,

            "payer": {
                "identification": {
                    "number": "123456789",
                    "type": "other"
                    },
                "name": first_name,
                "surname": last_name,
                "email": email,
                "phone": {
                    "area_code": "+56" ,
                    "number": telephone_number,
                },
                 "address": {
                "street_name": address_line_1,
                "street_number": "",
                "zip_code": postal_zip_code,
                }
                 
            },
           
            
        }
        print("-------------------------------inicio envio de preferencia ---------------------------")
        sdk = mercadopago.SDK(os.environ.get('TOKENMERCADOPAGOTEST'))
        print(os.environ.get('TOKENMERCADOPAGOTEST'))
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        #merchant_id = sdk.merchant_order().get()
        print(preference)
        #crear orden
        #try:
        print('------------------------------begin-order-----------------------------')
        if orderKey in data:
            print('----repaymentorder-------')
            return Response({'response': preference}, status=status.HTTP_200_OK)
        else:
            if user.is_anonymous is False:
                
                print('------------------------------user-session-order-----------------------------')
                order.user = user
            else:
                order.email = email
    

            
            order.amount=total_amount
            order.full_name=first_name + ' ' + last_name
            order.address_line_1=address_line_1
            order.city=city
            order.region=state_province_region
            order.postal_zip_code=postal_zip_code
            order.telephone_number=telephone_number
            print(shipping)
            order.shipping_id=shipping   
            order.save()       
            print('-------------------------end-order-----------------------------')
            
            if user.is_anonymous is False:
                cart = Carrito.objects.get(user=user)
                carrito_items = CarritoItem.objects.filter(carrito=cart)
                for cart_item in carrito_items:
                    try:
                        # agarrar el producto
                        product = Product.objects.get(id=cart_item.product.id)

                        OrderItem.objects.create(
                            product=product,
                            order=order,
                            name=product.name,
                            price=cart_item.product.price,
                            )
                    except:
                        return Response(
                            {'error': 'Transaction succeeded and order created, but failed to create an order item'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                            )
            else:
                print("---------agregar productos a la orden ----------")
                try:
                    for num in range(0,len(products)):
                        products_dict_a=products[num]
                        producto=products_dict_a['product']
                        product = Product.objects.get(id=producto['id'])
                        OrderItem.objects.create(
                            product=product,
                            order=order,
                            name=product.name,
                            price=product.price,
                            )
                except Exception:
                    print('el error es:' + str(Exception))
                    return Response(
                        {'error': 'Transaction succeeded and order created, but failed to create an order item'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            return Response({'response': preference}, status=status.HTTP_200_OK)
            
class PaymentsBricks(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        sdk = mercadopago.SDK("ACCESS_TOKEN")
        data=self.request.data
        user=self.request.user
        orderKey='orderId'
        print(data)
        print("---payment----")
        shipping_id = str(data['shipping_id'])
        shipping=Shipping.objects.get(id=shipping_id)
        total_amount = 0
        items = []
        if user.is_anonymous is False:
            profile_id = int(data['profile_id'])
            print(profile_id)
            profile_address = UserProfile.objects.get(id=profile_id)
            email=user.email
            first_name = user.first_name
            last_name = user.last_name
            address_line_1 = profile_address.address_line_1
            city=profile_address.city
            state_province_region =profile_address.country_region
            postal_zip_code =profile_address.zipcode
            telephone_number =profile_address.phone
            cart = Carrito.objects.get(user=user)
            if not CarritoItem.objects.filter(carrito=cart).exists():
                return Response(
                    {'error': 'No tienes productos en tu carrito'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            products = CarritoItem.objects.filter(carrito=cart)
            for product in products:
                producto= Product.objects.get(id=product.product.id)
                print(producto)
                productos = {}
                productos['id'] = producto.id
                productos['title'] = producto.name
                productos['currency_id'] = 'CLP'
                productos['description'] = producto.description
                productos['category_id'] = producto.category.id
                productos['quantity'] = 1
                productos['unit_price'] = float(producto.price)
                total_amount += float(producto.price)
                items.append(productos)
        else:

            email=data['email']
            first_name = data['first_name']
            last_name = data['last_name']
            address_line_1 = data['address_line_1']
            city = data['city']
            state_province_region = data['state_province_region']
            postal_zip_code = data['postal_zip_code']
            telephone_number = data['telephone_number']
            products = data['items']
            if products is None:
                return Response(
                    {'error': 'No tienes productos en tu carrito'},                            status=status.HTTP_404_NOT_FOUND
                    )

                for num in range(0,len(products)):
                    productos = { }
                        
                    products_dict=products[num]
                    product=products_dict['product']
                    productos['id'] = product['id']
                    productos['title'] = str(product['name'])
                    productos['currency_id'] = 'CLP'
                    productos['description'] = str(product['description'])
                    productos['category_id'] = str(product['category'])
                    productos['quantity'] = 1
                    productos['unit_price'] = float(product['price'])
                    total_amount += float(product['price'])
                    items.append(productos)

            
                    
                
        print("crea la orden")
        order = Order.objects.create()
         
            

        request_options = mercadopago.config.RequestOptions()
        request_options.custom_headers = {
            'x-idempotency-key': '<SOME_UNIQUE_VALUE>'
            }
        
        payment_data = {
            "transaction_amount": float(request.POST.get("transaction_amount")),
            "token": request.POST.get("token"),
            "description": request.POST.get("description"),
            "installments": int(request.POST.get("installments")),
            "payment_method_id": request.POST.get("payment_method_id"),
            "payer": {
                "email": request.POST.get("cardholderEmail"),
                "identification": {
                    "type": request.POST.get("identificationType"), 
                    "number": request.POST.get("identificationNumber")
                },
                "first_name": request.POST.get("cardholderName")
            }
        }

        payment_response = sdk.payment().create(payment_data, request_options)
        payment = payment_response["response"]

        print(payment)


class MercadoPagoResponse(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        sdk = mercadopago.SDK(os.environ.get('TOKENMERCADOPAGOTEST'))
        data = self.request.data
        print(data)
        try:
            id=data['data']['id']
            print(id)
            paymentRef = sdk.payment().get(id)
            print("paymentsdkget")
            print(paymentRef)
         
         
            externalRef = paymentRef['response']['external_reference']
            print(externalRef)
               
            if(Order.objects.filter(id=externalRef).exists()):
                order = Order.objects.get(id=externalRef)
                print(order)
            else:
                print('orden no encontrada')
                return Response({'error':'No se encontro la orden'}, status=status.HTTP_404_NOT_FOUND)
                    
                
            Status = paymentRef['response']['status']
            if(Status=='approved'):
                order.status = Order.OrderStatus.processed
                order.save()
                print('---------payments exist check---------------------------------------------')
                if Payments.objects.filter(payment_id=id).exists():
                    print("pago existente error" + str(Payments.objects.get(payment_id=id)))
                    return Response({'error': "pago existente error"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    print("crear pago:")
                    print(id)
                    payment = Payments.objects.create(payment_id=id, order = order)
                    print("pago creado")
                    if order.user is not None:
                        print('dentro de algoritmo de sincronicacion de carrito y productos con usuario')
                        carrito = Carrito.objects.get(user=order.user)
                        orderitems = OrderItem.objects.filter(order=order)
                        carritoitems = CarritoItem.objects.filter(carrito=carrito)
                        print("inicio ciclo for con usuario")
                        for items in orderitems:
                            items.delete()
                            if not Product.objects.filter(id=items.product.id).exists():
                                return Response({'error':"error al encontrar el producto"},status=status.HTTP_404_NOT_FOUND)
                            product = Product.objects.get(id=items.product.id)
                            product.sold=True
                            product.save()
                            print("inicio ciclo carrito con usuario")
                            for itemscar in carritoitems:
                                if items.product.id == itemscar.product.id:
                                    itemscar.delete()
                                    carrito.total_items += -1

                        
                        
                        carrito.save()
                    else:
                        print("pago sin usuario")
                        order_items = OrderItem.objects.filter(order=order)
                        print(order_items)
                        for items in order_items:
                            product = Product.objects.get(id=items.product.id)
                            print(product)
                            product.sold=True
                            product.save()
                    
                print(order)
                print('----------------------------')
                    
            elif(Status=='rejected'):
                order.save()
            else:
                order.save()
            
        except Exception as e:
            print(str(e))
            print('exception^')
        try:
            topic = data['topic']
            if topic == 'payment':
                print(topic + data['data']['id'])
            elif topic == 'merchant_order':
                print(data['resource'])
        except:
            print('no topic')
        return Response({'status':"finish"},status=status.HTTP_200_OK)
           # externalReference = reponse_dict['external reference']
            #order = Order.objects.get(id=externalReference)
            #order.transaction_id = request.GET.get('id')
            #order.save()
            #paymentRef = sdk.payment().get(request.GET.get('data.id'))
            #print('---------impresion pago id-----------------')
            #payresponse = paymentRef['response']
            #print(paymentRef['response'])
            #orderInfo=payresponse['order'] 
            #order = Order.objects.get(transaction_id=orderInfo['id'],)
            #if payresponse['status'] == 'approved':
            #   order.status = Order.OrderStatus.processed
             #   order.save()
              #  print("-------------payments exist check---------------------------------------------")
             #   if Payments.objects.filter(payment_id=request.GET.get('data.id')).exists():
             #       print("pago existente error" + str(Payments.objects.get(payment_id=request.GET.get('data.id'))))
             #   else:
             #       print("no in")
             #       payment = Payments.objects.create(payment_id=request.GET.get('data.id'), order = order)
             #   print(order.user)
             #   if order.user is not Null:
             #       print('user in')
             #       carrito = Carrito.objects.get(user=order.user)
             #       orderitems = OrderItem.objects.filter(order=order)
             #       carritoitems = CarritoItem.objects.filter(carrito=carrito)
             #       for items in orderitems:
             #           items.delete()
             #           product = Product.objects.get(id=items.product.id)
             #           product.sold=True
             #           product.save()
             #           for itemscar in carritoitems:
             #               if item.product.id == itemscar.product.id:
             #                   itemscar.delete()
             #                   carrito.total_items += -1

                    
                    
                #    carrito.save()
                #else:
                #    print("in")
                #    order_items = OrderItem.objects.filter(order=order)
                #    print(order_items)
                #    for items in order_items:
                #        product = Product.objects.get(id=items.product.id)
                #        print(product)
                #        product.sold=True
                #        product.save()
                    
                #print(order)
                #print('----------------------------')
            #elif payresponse['status']=='failure':
             #   print("fallo server1")
            #elif payresponse['status']=='rejected':
            #    order.status = Order.OrderStatus.refused
            #    order.save()
            #    print("pago rechazado")
                
            #elif payresponse['status']=='no funds':
                #print("fallo server3")
            #return Response({'success': True}, status=status.HTTP_200_OK)
    

class StatusPaymentView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self,request, format=None):
        return Response ({"status": order.status}, status=status.HTTP_200_OK)

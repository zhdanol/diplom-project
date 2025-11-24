from django.conf import settings
from django.shortcuts import get_object_or_404
import json 
from distutils.util import strtobool
from rest_framework.request import Request
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q, F, Sum
from django.http import JsonResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from ads.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, Contact, ConfirmEmailToken
from ads.serializers import UserSer, CategorySer, ShopSer, ProductInfoSer, OrderItemSer, OrderSer, ContactSer
import yaml
from ads.tasks import send_email

# Create your views here.
load_json=json.loads
        
class RegisterUser(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        if {'first_name', 'last_name', 'email', 'password', 'company','position'}.issubset(self.request.data):
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_ = []
                for item in password_error:
                    error_.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_}}, status=status.HTTP_403_FORBIDDEN)
            else:
                user_ser = UserSer(data=request.data)
                if user_ser.is_valid():
                    user = user_ser.save()
                    user.set_password(request.data['password'])
                    user.save()
                    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)
                    from django.core.mail import send_mail
                    send_email('Confirmation of registration',
                               f'Your confirmation token {token.key}',
                               'olegzdanov87@gmail.com', [user.email],
                               fail_silently=False,
                               )
                    
                    return JsonResponse({'Status': True, 'Token for email confirmation': token.key}, status=status.HTTP_201_CREATED)
                else:
                    return JsonResponse({'Status': False, 'Errors': user_ser.errors}, status=status.HTTP_403_FORBIDDEN)
        
        return JsonResponse({'Status': False, 'Errors': 'All necessary argument are not specified'}, status=status.HTTP_400_BAD_REQUEST)
    

class EmailConfirmUser(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        if {'email', 'token'}.issubset(request.data):
            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],key=request.data['token']).first()
            
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Error': 'The token or email is incorrectly'})
        
        return JsonResponse({'Status': False, 'Error': 'All necessary argument are not specified'})
    
    
class LoginUser(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        if not {'email', 'password'}.issubset(request.data):
            return JsonResponse({'Status': False, 'Errors': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, username=request.data['email'], password=request.data['password'])
        if user is not None:
            if user.is_active:
                token, _ = Token.objects.get_or_create(user=user)
                return JsonResponse({
                    'Status': True,
                    'Token': token.key,
                     'User': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'type': user.type
                        }
                    })
            else:
                return JsonResponse({'Status': False, 'Errors': 'failed to authorize'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return JsonResponse({'Status': False, 'Errors': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
        
        
class ProductInfoView(ListAPIView):
    permission_classes = [IsAuthenticated]
    
    queryset = ProductInfo.objects.filter(quantity__gt=0).select_related('product', 'shop')
    serializer_class = ProductInfoSer
    filter_fields = ['shop', 'product_category']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        shop_id = self.request.query_params.get('shop_id')
        category_id = self.request.query_params.get('category_id')
        
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)
        
        return queryset
    
class CategoryView(APIView):
    queryset = Category.objects.all()
    serializer_class = CategorySer


class ShopView(APIView):
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSer


class CartView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)
        
        cart = Order.objects.filter(
            user_id=request.user.id, status='cart').prefetch_related(
                'ordered_items__product_info').annotate(
                    total_sum=Sum(F('ordered_items__quantity')* F('ordered_items__product_info__price'))).first()
        if cart:
            serializer = OrderSer(cart)
            return Response(serializer.data)
        return Response({'Status': True, 'Cart': {}})
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)
        
        items = request.data.get('items')
        if 'items':
            try:
                items_dict = load_json(items) if isinstance(items, str) else items
            except ValueError as err:
                return JsonResponse({'Status': False, 'Errors': f'Invalid request{err}'})
            else:
                cart, _= Order.objects.get_or_create(user_id=request.user.id,status='cart')
                
                objects_create = 0
                for item_data in items_dict:
                    try:
                        product_info = ProductInfo.objects.get(id=item_data['product_info'])
                        order_item, created = OrderItem.objects.get_or_create(
                            order=cart,
                            product_info=product_info,
                            defaults={'quantity': item_data['quantity']}
                        )
                        if not created:
                            order_item.quantity = item_data['quantity']
                            order_item.save()
                        objects_create += 1
                    except IntegrityError as err:
                        return JsonResponse({'Status': False, 'Errors': str(err)})                            
                    except KeyError:
                        return JsonResponse({'Status': False, 'Errors': 'Invalid item format'})
                        
                return JsonResponse({'Status': True, 'Objects_create': objects_create,}, status=status.HTTP_201_CREATED)
            
        return JsonResponse({'Status': False, 'Errors': 'All arguments are not specifed'}, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)
        
        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_list = load_json(items_sting) if isinstance(items_sting, str) else items_sting
            except ValueError as err:
                return JsonResponse({'Status': False, 'Errors': f'Invalid request{err}'})
            else:
                cart, _ = Order.objects.get_or_create(user_id=request.user.id, status='cart')
                
                objects_update = 0
                for order_item in items_list:
                    if isinstance(order_item.get('id'), int) and isinstance(order_item.get('quantity'), int):
                        updated = OrderItem.objects.filter(
                            order_id = cart.id,
                            product_info_id=order_item['id']).update(quantity=order_item['quantity'])
                        objects_update += updated
                        
                return JsonResponse({'Status': True, 'Objects create': objects_update})
            
        return JsonResponse({'Status': False, 'Error': 'Argument are not specified'}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)
        
        items = request.data.get('items')
        if items:
            items_list = items.split(',') if isinstance(items, str) else items
            cart, _ = Order.objects.get_or_create(user_id=request.user.id, status='cart')
            query = Q()
            objects_deleted = False
            
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=cart.id, id=int(order_item_id))
                    objects_deleted = True
                    
            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Objects create': deleted_count}, status=status.HTTP_200_OK)
            
        return JsonResponse({'Status': False, 'Error': 'Arguments are not specified'}, status=status.HTTP_400_BAD_REQUEST)


class PartnerState(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'For shops only'}, status=status.HTTP_403_FORBIDDEN)
        
        shop = request.user.shop
        serializer = ShopSer(shop)
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'For only shop'}, status=status.HTTP_403_FORBIDDEN)
        
        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({'Status': True}, status=status.HTTP_200_OK)
            except ValueError as err:
                return JsonResponse({'Status': False, 'Errors': str(err)})
            
        return JsonResponse({'Status': False, 'Errors': 'Arguments are not specified'})
    
    
class PartnerOrders(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'For only shops'}, status=status.HTTP_403_FORBIDDEN)
        
        order = Order.objects.filter(
            ordered_items__product_info__shop__user_id = request.user.id).exclude(status='cart').prefetch_related(
                'ordered_items__product_info').select_related('contact').annotate(
                    total_sum=Sum(F('ordered_items__quantity')* F('ordered_items__product_info__price'))).distinct()
                
        serializer = OrderSer(order, many=True)
        from django.core.mail import send_mail
        send_mail(
        'Order status update',
        'The order has been processed',
        'olegzdanov87@gmail.com',
        [request.user.email],
        fail_silently=False,
        )
        return Response(serializer.data)    
    
    
class PartnerUpdate(APIView):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=status.HTTP_403_FORBIDDEN)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'For only shops'}, status=status.HTTP_403_FORBIDDEN)
        
        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as err:
                return JsonResponse({'Status': False, 'Error': str(err)})
            else:
                stream = get(url).content
                data = yaml.safe_load(stream)

                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                
                for category in data['categories']:
                    category_object,_ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ =Product.objects.get_or_create(name=item['name'], category_id=item['category'])
                    product_info = ProductInfo.objects.create(
                        product_id=product.id,
                        model=item.get('model'),
                        price=item['price'],
                        price_rrc=item['price_rrc'],
                        quantity=item['quantity'],
                        shop_id=shop.id)
                    
                    for name, value in item.get('parameters').items():
                        parameter_objects, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_objects.id,
                                                        value=value)
                        
                return JsonResponse({'Status': True}, status=status.HTTP_200_OK)
            
        return JsonResponse({'Status': False, 'Errors': 'not specified'}, status=status.HTTP_400_BAD_REQUEST)       
     
     
class ContactView(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)
        
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSer(contact, many=True)
        return Response(serializer.data)
        
    def post(self, request, *args, **kwargs):
        if {'city', 'street', 'phone'}.issubset(request.data):
            request.POST._mutable = True
            request.data.update({'user':request.user.id})
            serializer = ContactSer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True}, status=status.HTTP_201_CREATED)
            else:
                return JsonResponse({'Status': False, 'Errors':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
        return JsonResponse({'Status': False, 'Error': 'Argument are not specified'}, status=status.HTTP_400_BAD_REQUEST)
        
    def put(self, request, *args, **kwargs):
        if {'id'}.issubset(request.data):
            try:
                contact = get_object_or_404(Contact, pk=int(request.data['id']))
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Invalid failed type ID'}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ContactSer(contact, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True}, status=status.HTTP_200_OK)
            
            return JsonResponse({'Status': False, 'Error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        return JsonResponse({'Status': False, 'Error': 'Argument are not specified'}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, *args, **kwargs):
        if {'items'}.issubset(request.data):
            for item in request.data['items'].split(','):
                try:
                    contact = get_object_or_404(Contact, pk=int(item))
                    contact.delete()
                except ValueError:
                    return JsonResponse({'Status': False, 'Error': 'invalid argument(items)'}, status=status.HTTP_400_BAD_REQUEST)
                
                except ObjectDoesNotExist:
                    return JsonResponse({'Status': False, 'Error': f'No contact{item}'}, status=status.HTTP_400_BAD_REQUEST)
                
            return JsonResponse({'Status': True}, status=status.HTTP_200_OK)
        return JsonResponse({'Status':False, 'Error': 'Argument are not specified'}, status=status.HTTP_400_BAD_REQUEST)


class OrderView(APIView):
    def get(self, request, *args, **kwargs):
        order = Order.objects.filter(
            user_id=request.user.id).exclude(status='cart').prefetch_related(
                'ordered_items__product_info').select_related('contact').annotate(
                    total_sum=Sum(F('ordered_items__quantity')* F('ordered_items__product_info__price'))
                ).distinct().order_by('-dt')
        serializer = OrderSer(order, many=True)
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        if {'id', 'contact'}.issubset(request.data):
            try:
                order = Order.objects.get(
                    user_id = request.user.id, id=request.data['id'],
                    status='cart')
                order.contact_id = request.data['contact']
                order.status = 'new'
                order.save()
                
                from ads.tasks import send_invoice_admin
                invoice_result = send_invoice_admin(order.id)
                print(f' Накладная: {invoice_result}')
                
                return JsonResponse({
                    'Status': True,
                    'Message': 'Заказ оформлен. Накладная отправлена администратору.'
                })
                
            except Order.DoesNotExist:
                return JsonResponse({'Status': False, 'Errors': 'Order not found'})
            
            except IntegrityError as err:
                return JsonResponse({'Status': False, 'Errors': f'Argument incorrectly{err}'}, status=status.HTTP_400_BAD_REQUEST)
            
        return JsonResponse({'Status': False, 'Errors': 'Required fields are not specified'}, status=status.HTTP_400_BAD_REQUEST)

            
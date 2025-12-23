from django.conf import settings
from django.shortcuts import get_object_or_404
import json
from ads.utils import strtobool
from rest_framework.request import Request
from django.contrib.auth import authenticate, login
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
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from ads.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, Contact, ConfirmEmailToken, User, ProductImage
from ads.serializers import UserSer, CategorySer, ShopSer, ProductInfoSer, OrderItemSer, OrderSer, ContactSer, ProductImageSer
import yaml
from .tasks import send_email, send_order_confirmation, send_invoice_admin
from social_django.utils import psa
from social_django.models import UserSocialAuth
from rest_framework.decorators import api_view, permission_classes
import logging
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
import time
from .throttling import (
    RegistrationThrottle, LoginThrottle, PartnerThrottle, ProductUpdateTrhottle,
    SocialAuthThrottle, BurstRateThrottle, SustainedRateThrottle
)

logger = logging.getLogger(__name__)
        

class SocialLoginProviderView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            logger.info('SocialLoginProviderView called')
            
            providers = []
            
            google_key = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
            
            if google_key and google_key.strip() and google_key not in ['', 'ваш-google-client-id']:
                providers.append({
                    'name': 'google',
                    'display_name': 'Google',
                    'auth_url': '/social-auth/login/google-oauth2/',
                    'icon': 'https://img.icons8.com/color/48/000000/google-logo.png',
                })
            
            github_key = getattr(settings, 'SOCIAL_AUTH_GITHUB_KEY', '')
            
            if github_key and github_key.strip() and github_key not in ['', 'ваш-github-client-id']:
                providers.append({
                    'name': 'github',
                    'display_name': 'Github',
                    'auth_url': '/social-auth/login/github/',
                    'icon': 'https://img.icons8.com/ios-filled/48/000000/github.png'
                })
            response_data = {
                'Status': True,
                'provider': providers,
                'count': len(providers),
                'settings_info':{
                    'google_configured': bool(google_key and google_key.strip() and google_key not in ['', 'ваш-google-client-id']),
                    'github_configured': bool(github_key and github_key.strip() and github_key not in ['', 'ваш-github-client-id']),
                    'google_key_preview': f'{google_key[:10]}...' if google_key and len(google_key) > 10 else google_key,
                    'github_key_preview': f'{github_key[:10]}...' if github_key and len(github_key) > 10 else github_key,
                }
            }
            
            logger.info(f'Returning {len(providers)} social providers')
            return Response(response_data)
        
        except Exception as ex:
            logger.error(f'Error in SocialLoginProvidersView: {str(ex)}', exc_info=True)
            return Response({
                'Status': False,
                'Error': 'Не удалось получить список провайдеров',
                'Debug': str(ex) if settings.DEBUG else None
            }, status=500)
    
class SocialLoginCallbackView(APIView):
    permission_classes = [AllowAny]
    
    @psa('social:complete')
    def post(self, request, *args, **kwargs):
        provider = request.data.get('provider')
        access_token = request.data.get('access_token')
        
        if not provider or not access_token:
            return Response({
                'Status': False,
                'Error': 'Требуется provider и access_token'
            }, status=400)
        
        try:
            backend = request.backend
            user = backend.do_auth(access_token)
            if user and user.is_active:
                token, created = Token.objects.get_or_create(user=user)
                
                try:
                    social_user = UserSocialAuth.objects.get(user=user, provider=provider)
                    extra_data = social_user.extra_data
                    
                except UserSocialAuth.DoesNotExist:
                    extra_data = {}
                    
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                return Response({
                    'Status': True,
                    'Token': token.key,
                    'User': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'type': user.type,
                        'company': user.company,
                        'position': user.position
                    },
                    'SocialData': {
                        'provider': provider,
                        'uid': extra_data.get('id', ''),
                        'picture': extra_data.get('picture', ''),
                        'locale': extra_data.get('locale', '')
                    }
                })
            else:
                return Response({
                    'Status': False,
                    'Error': 'Не удалось аутентифицировать пользователя'
                }, status=401)
                
        except Exception as e:
            return Response({
                'Status': False,
                'Error': f'Ошибка при обработке социальной авторизации: {str(e)}'
            }, status=500)

    def get(self, request, *args, **kwargs):
        try:
            social_data = request.session.get('social_auth_data', {})
            if social_data:
                if 'social_auth_data' in request.session:
                    del request.session['social_auth_data']
                    
                user_id = social_data.get('user_id')
                provider = social_data.get('provider')
                
                if user_id:
                    try:
                        user = User.objects.get(id=user_id)
                        token, created = Token.objects.get_or_create(user=user)
                        
                        from django.shortcuts import redirect
                        frontend_url = f'http://localhost:3000/auth/callback?token={token.key}&user_id={user.id}'
                        return redirect(frontend_url)
                    except User.DoesNotExist:
                        pass
            return Response({
                'Status': False,
                'Error': 'Не удалось завершить авторизацию'
            }, status=400)
        except Exception as ex:
            return Response({
                'Status': False,
                'Error': f'Ошибка при обработке callback: {str(ex)}'
            }, status=500)
    
    
@api_view(['POST'])
@permission_classes([AllowAny])
def social_auth(request, backend):
    token = request.data.get('access_token')
    user = request.backend.do_auth(token)
    
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'type': user.type,
        })
    else:
        return Response({'error': 'Authentication failed'}, status=400)
    
    
class SentryView(APIView):
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        if not request.user.is_superuser:
            return Response({
                'error': 'Требуются права администратора',
            }, status=status.HTTP_403_FORBIDDEN)
            
        error_type = request.query_params.get('type', 'division')
        try:
            if error_type == 'division':
                result = 1 / 0
            elif error_type == 'index':
                items = [1, 2, 3]
                result = items[10]
            elif error_type == 'key':
                data = {'a': 1}
                result = data['b']
            elif error_type == 'log':
                logger.error("Тестовая ошибка в логах", exc_info=True)
                return Response({
                    "message": "Ошибка записана в логи",
                    "error_type": error_type
                })
            elif error_type == 'custom':
                raise ValueError("Тестовое кастомное исключение для Sentry")
            else:
                return Response({
                    "available_types": [
                        "division", "index", "key", "import", "log", "custom"
                    ],
                    "usage": "/api/test-sentry/?type=division"
                })
            
            return Response({"result": result})
        
        except Exception as ex:
            from sentry_sdk import capture_exception
            capture_exception(ex)
            
            return Response({
                "error": str(ex),
                "type": error_type,
                "message": "Исключение отправлено в Sentry"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PerformanceView(APIView):
    
    def get(self, request):
        import sentry_sdk 
        import time
        from sentry_sdk import start_transaction
        
        with start_transaction(op="task", name="performance_test") as transaction:
            time.sleep(0.1)
            
            with transaction.start_child(op="db_query", description="get_users"):
                time.sleep(0.2)
                
            with transaction.start_child(op="external_api", description="call_api"):
                time.sleep(0.3)
                
        return Response({
            "message": "Транзакция завершена",
            "trace_id": sentry_sdk.Hub.current.scope.span.trace_id if sentry_sdk.Hub.current.scope.span else None
        })

# Регистрация нового пользователя
class RegisterUser(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegistrationThrottle, BurstRateThrottle]
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
                    email_result = send_email.delay(
                        'Подтверждение регистрации',
                        f'Ваш токен для подтверждения: {token.key}',
                        user.email
                    )
                    print(f'Email sent: {email_result}')
                    
                    return JsonResponse({'Status': True, 'Token for email confirmation': token.key}, status=status.HTTP_201_CREATED)
                else:
                    return JsonResponse({'Status': False, 'Errors': user_ser.errors}, status=status.HTTP_403_FORBIDDEN)
        
        return JsonResponse({'Status': False, 'Errors': 'All necessary argument are not specified'}, status=status.HTTP_400_BAD_REQUEST)
    

# Подтверждение email
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
    
    
# Авторизация пользователя
class LoginUser(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle, BurstRateThrottle]
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
        
class ProductImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [BurstRateThrottle]
    
    @method_decorator(cache_page(60*15))
    def get(self, request, product_id=None, pk=None):
        if pk:
            image = get_object_or_404(ProductImage, pk=pk, product__product_infos__shop__user=request.user)
            serializer = ProductImageSer(image)
            return Response(serializer.data)
        
        product = get_object_or_404(Product, pk=product_id)
        images = product.images.all().order_by('order', '-is_main', 'created_at')
        serializer = ProductImageSer(images, many=True)
        return Response(serializer.data)        

    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        if request.user.type != 'shop':
            return Response(
                {'Error': 'Только магазины могут загружать изображения'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not product.product_infos.filter(shop__user=request.user).exists():
            return Response(
                {'Error': 'У вас нет прав на редактирование этого товара'},
                status=status.HTTP_403_FORBIDDEN
            )
        data = request.data.copy()
        data['product'] = product.id
        
        serializer = ProductImageSer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        image = get_object_or_404(ProductImage, pk=pk, product__product_infos__shop__user=request.user)
        serializer = ProductImageSer(image, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        image = get_object_or_404(ProductImage, pk=pk, product__product_infos__shop__user=request.user)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProductMainImageView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle]
    
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response(
                {'Error': 'Не указан ID изображения'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not product.product_infos.filter(shop__user=request.user).exists():
            return Response(
                {'error': 'У вас нет прав на редактирование этого товара'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            image = product.images.get(pk=image_id)
            image.is_main = True
            image.save()
            
            return Response({'status': 'success', 'message': 'Главное изображение обновлено'})
        
        except ProductImage.DoesNotExist:
            return Response(
                {'error': 'Изображение не найдено'},
                status=status.HTTP_404_NOT_FOUND
            )

# Каталог товаров        
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


# Список категорий    
class CategoryView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategorySer


# Список магазинов
class ShopView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSer


# Работа с корзиной покупок
class CartView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            cart = Order.objects.filter(user_id=request.user.id, status='cart').first()
            
            if cart:
                return Response({
                    'id': cart.id,
                    'status': cart.status,
                    'message': 'Cart exists'
                })
            return Response({'Status': True, 'Cart': {}})
            
        except Exception as e:
            return JsonResponse({'Status': False, 'Error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)
        
        items = request.data.get('items')
        if items:
            try:
                items_dict = json.loads(items) if isinstance(items, str) else items
            except ValueError as err:
                return JsonResponse({'Status': False, 'Errors': f'Invalid request{err}'})
            else:
                cart, _= Order.objects.get_or_create(user_id=request.user.id,status='cart')
                
                objects_create = 0
                for item_data in items_dict:
                    try:
                        product = ProductInfo.objects.get(id=item_data['product_id'])
                        order_item, created = OrderItem.objects.get_or_create(
                            order=cart,
                            product=product,
                            shop=product.shop,
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
                items_list = json.loads(items_sting) if isinstance(items_sting, str) else items_sting
            except ValueError as err:
                return JsonResponse({'Status': False, 'Errors': f'Invalid request{err}'})
            else:
                cart, _ = Order.objects.get_or_create(user_id=request.user.id, status='cart')
                
                objects_update = 0
                for order_item in items_list:
                    if isinstance(order_item.get('id'), int) and isinstance(order_item.get('quantity'), int):
                        updated = OrderItem.objects.filter(
                            order_id = cart.id,
                            product_id=order_item['id']).update(quantity=order_item['quantity'])
                        objects_update += updated
                        
                return JsonResponse({'Status': True, 'Objects_update': objects_update})
            
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
                return JsonResponse({'Status': True, 'Objects_deleted': deleted_count}, status=status.HTTP_200_OK)
            
        return JsonResponse({'Status': False, 'Error': 'Arguments are not specified'}, status=status.HTTP_400_BAD_REQUEST)


# Управление статусом магазина
class PartnerState(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PartnerThrottle]
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
    

# Заказы магазина    
class PartnerOrders(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PartnerThrottle]
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'For only shops'}, status=status.HTTP_403_FORBIDDEN)
        
        order = Order.objects.filter(
            order_items__product__shop__user_id = request.user.id).exclude(status='cart').prefetch_related(
                'order_items__product').select_related('contact').annotate(
                    total_sum=Sum(F('order_items__quantity')* F('order_items__product__price'))).distinct()
                
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
    

# Обновление каталога товаров    
class PartnerUpdate(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PartnerThrottle, ProductUpdateTrhottle]
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
                        name=item.get('name', ''),
                        price=item['price'],
                        price_rrc=item['price_rrc'],
                        quantity=item['quantity'],
                        shop_id=shop.id)
                    
                    for name, value in item.get('parameters', {}).items():
                        parameter_objects, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_objects.id,
                                                        value=value)
                        
                return JsonResponse({'Status': True}, status=status.HTTP_200_OK)
            
        return JsonResponse({'Status': False, 'Errors': 'not specified'}, status=status.HTTP_400_BAD_REQUEST)       
     

# Контакты пользователя     
class ContactView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SustainedRateThrottle]
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


# Просмотр и оформление заказов
class OrderView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SustainedRateThrottle]
    def get(self, request, *args, **kwargs):

        order_id = kwargs.get('pk')
        
        if order_id:

            try:
                order = Order.objects.get(id=order_id, user_id=request.user.id)
                return Response({
                    'id': order.id,
                    'status': order.status,
                    'dt': order.dt,
                    'message': 'Order details'
                })
            except Order.DoesNotExist:
                return JsonResponse({'Status': False, 'Errors': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        else:

            try:
                orders = Order.objects.filter(user_id=request.user.id).exclude(status='cart').order_by('-dt')
                orders_data = []
                for order in orders:
                    orders_data.append({
                        'id': order.id,
                        'status': order.status,
                        'dt': order.dt
                    })
                return Response(orders_data)
            except Exception as e:
                return JsonResponse({'Status': False, 'Error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, *args, **kwargs):
        if {'id'}.issubset(request.data):
            try:
                order = Order.objects.get(
                    user_id=request.user.id, 
                    id=request.data['id'],
                    status='cart'
                )

                order.status = 'new'
                order.save()
                
                confirmation_result = send_order_confirmation.delay(order.id)
                print(f"Order confirmation: {confirmation_result}")
                
                invoice_result = send_invoice_admin.delay(order.id)
                print(f"Invoice to admin: {invoice_result}")
                
                return JsonResponse({
                    'Status': True,
                    'Message': 'Заказ оформлен. Накладная отправлена администратору.'
                })
                
            except Order.DoesNotExist:
                return JsonResponse({'Status': False, 'Errors': 'Order not found'})
            
            except IntegrityError as err:
                return JsonResponse({'Status': False, 'Errors': f'Argument incorrectly{err}'}, status=status.HTTP_400_BAD_REQUEST)
            
        return JsonResponse({'Status': False, 'Errors': 'Required fields are not specified'}, status=status.HTTP_400_BAD_REQUEST)
            
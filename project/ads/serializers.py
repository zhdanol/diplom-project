from rest_framework import serializers
from django.contrib.auth import authenticate
from ads.models import Category, Shop, Product, ProductInfo, User, OrderItem, Order, ProductParameter, Contact, ProductImage
from social_django.models import UserSocialAuth

class SocialAuthSer(serializers.Serializer):
    access_token = serializers.CharField(required=True)
    backend = serializers.CharField(required=True)
    
class SocialProviderSerializer(serializers.Serializer):
    name = serializers.CharField()
    display_name = serializers.CharField()
    auth_url = serializers.CharField()
    icon = serializers.URLField()

class UserSocialAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSocialAuth
        fields = ['id', 'provider', 'uid', 'extra_data', 'created']
        read_only_fields = fields

class SocialAuthResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    token = serializers.CharField()
    user = serializers.DictField()
    social = serializers.DictField()

# Валидация данных для входа в систему
class UserLoginSer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Неверные данные')
        else:
            raise serializers.ValidationError('Необходимо указать email и пароль')
        
        attrs['user'] = user
        return attrs


# Сериализация адресов и контактов доставки
class ContactSer(serializers.ModelSerializer):
    full_address = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Contact
        fields = ['id', 'type', 'user', 'value', 'country', 'region', 'city',
                  'street', 'house', 'building', 'structure', 'apartment', 'phone',
                  'full_address', 'is_main', 'created_at', 'updated_at']
        
    def get_full_address(self, obj):
        return obj.get_full_address()

# Отображение данных пользователя с контактами        
class UserSer(serializers.ModelSerializer):
    contacts = ContactSer(read_only=True, many=True)        
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'company', 'position', 'type', 'contacts']


# Создание нового пользователя с проверкой пароля        
class UserRegisterSer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'password_confirm']
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError('Пароли не совпадают')
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name',''),
            last_name=validated_data.get('last_name',''),
            type = 'buyer'
        )
        return user
    

# Базовые данные магазина
class ShopSer(serializers.ModelSerializer):
    
    class Meta:
        model = Shop
        fields = ['id', 'name', 'state']

# Список категорий для навигации
class CategorySer(serializers.ModelSerializer):
    
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductImageSer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    medium_url = serializers.SerializerMethodField()
    large_url = serializers.SerializerMethodField()
    web_url = serializers.SerializerMethodField()
    
    all_variants = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = [
            'id', 'product', 'image', 'image_url',
            'thumbnail_url', 'medium_url', 'large_url', 
            'web_optimized_url', 'all_variants',
            'is_main', 'alt_text', 'order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')
        
    def get_image_url(self, obj):
        return obj.image.url if obj.image else None
    
    def get_thumbnail_url(self, obj):
        return obj.thumbnail.url if hasattr(obj.thumbnail, 'url') else None
    
    def get_medium_url(self, obj):
        return obj.medium.url if hasattr(obj.medium, 'url') else None
    
    def get_large_url(self, obj):
        return obj.large.url if hasattr(obj.large, 'url') else None
    
    def get_web_optimized_url(self, obj):
        return obj.web_optimized.url if hasattr(obj.web_optimized, 'url') else None
    
    def get_all_variants(self, obj):
        return obj.get_all_variants()
    
    def validate(self, data):
        if data.get('is_main', False):
            product = data.get('product') or (self.instance.product if self.instance else None)
            if product:
                existing_main = ProductImage.objects.filter(
                    product=product, 
                    is_main=True
                ).exclude(pk=getattr(self.instance, 'pk', None))
                
                if existing_main.exists():
                    raise serializers.ValidationError({
                        'is_main': 'У этого товара уже есть главное изображение'
                    })
        return data

# Отображение товара с категорией
class ProductSer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'description', 'sku',
            'images', 'main_image_url', 'thumbnail_url'
        ]
    def get_main_image_url(self, obj):
        image = obj.get_main_image()
        return image.medium.url if image else None
    
    def get_thumbnail_url(self, obj):
        image = obj.get_main_image()
        return image.thumbnail.url if image else None

# Параметры товара        
class ProductParameterSer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()
    
    class Meta:
        model = ProductParameter
        fields = ['parameter', 'value']


# Детальная информация о товаре с ценами и параметрами
class ProductInfoSer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()
    
    product = ProductSer(read_only=True)
    parameters = ProductParameterSer(read_only=True, many=True, source='product_parameters')
    shop = ShopSer(read_only=True)
    images = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductInfo
        fields = ['id', 'product', 'shop', 'price', 'price_rrc', 'quantity', 'parameters', 'imeges']
        
    def get_images(self, obj):
        images = obj.product.images.all().order_by('order', '-is_main')
        return ProductImageSer(obj.product.images.all(), many=True).data
    
    def get_main_image(self, obj):
        main_image = obj.product.images.filter(is_main=True).first()
        if main_image:
            return {
                'thumbnail': main_image.thumbnail.url if hasattr(main_image.thumbnail, 'url') else None,
                'medium': main_image.medium.url if hasattr(main_image.medium, 'url') else None,
                'large': main_image.large.url if hasattr(main_image.large, 'url') else None,
            }
        return None

# Товар в корзине/заказе с расчетом стоимости        
class OrderItemSer(serializers.ModelSerializer):
    product_info = ProductInfoSer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_info', 'quantity', 'total_price']
    
    def get_total_price(self, obj):
        return obj.quantity * obj.product_info.price
    
# Для операций создания/обновления
class OrderItemCreateSer(OrderItemSer):
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_info', 'quantity', 'total_price']
        
    def get_total_price(self, obj):
        return obj.quantity * obj.product_info.price


# Детали заказа с товарами и общей суммой    
class OrderSer(serializers.ModelSerializer):
    order_items = OrderItemCreateSer(read_only=True, many=True)
    
    total_sum = serializers.SerializerMethodField()
    contact = ContactSer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_items', 'status', 'dt', 'total_sum', 'contact']
        
    def get_total_sum(self, obj):
        return sum(item.quantity*item.product_info.price for item in obj.order_items.all())

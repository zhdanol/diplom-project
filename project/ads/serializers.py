from rest_framework import serializers
from django.contrib.auth import authenticate
from ads.models import Category, Shop, Product, ProductInfo, User, OrderItem, Order, ProductParameter, Contact

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



class ContactSer(serializers.ModelSerializer):
    full_address = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Contact
        fields = ['id', 'type', 'user', 'value', 'country', 'region', 'city',
                  'street', 'house', 'building', 'structure', 'apartment', 'phone',
                  'full_address', 'is_main', 'created_at', 'updated_at']
        
    def get_full_address(self, obj):
        return obj.get_full_address()
        
class UserSer(serializers.ModelSerializer):
    contacts = ContactSer(read_only=True, many=True)        
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'company', 'position', 'type', 'contacts']
        
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
    

class ShopSer(serializers.ModelSerializer):
    
    class Meta:
        model = Shop
        fields = ['id', 'name', 'state']

class CategorySer(serializers.ModelSerializer):
    
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'category']
        
class ProductParameterSer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()
    
    class Meta:
        model = ProductParameter
        fields = ['parameter', 'value']

class ProductInfoSer(serializers.ModelSerializer):
    product = ProductSer(read_only=True)
    parameters = ProductParameterSer(read_only=True, many=True, source='product_parameters')
    shop = ShopSer(read_only=True)
    
    class Meta:
        model = ProductInfo
        fields = ['id', 'product', 'shop', 'price', 'price_rrc', 'quantity', 'parameters']
        
class OrderItemSer(serializers.ModelSerializer):
    product_info = ProductInfoSer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_info', 'quantity', 'total_price']
    
    def get_total_price(self, obj):
        return obj.quantity * obj.product_info.price
    
class OrderItemCreateSer(OrderItemSer):
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_info', 'quantity', 'total_price']
        
    def get_total_price(self, obj):
        return obj.quantity * obj.product_info.price
    
class OrderSer(serializers.ModelSerializer):
    ordered_items = OrderItemCreateSer(read_only=True, many=True)
    
    total_sum = serializers.SerializerMethodField()
    contact = ContactSer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'ordered_items', 'status', 'dt', 'total_sum', 'contact']
        
    def get_total_sum(self, obj):
        return sum(item.quantity*item.product_info.price for item in obj.ordered_items.all())

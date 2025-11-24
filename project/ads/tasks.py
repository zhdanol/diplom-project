from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail


def send_email(title, message, email, *args, **kwargs):
    email_list = list()
    email_list.append(email)
    try:
        msg = EmailMultiAlternatives(subject=title, body=message, from_email=settings.EMAIL_HOST_USER, to=email_list)
        msg.send()
        return f'{title}: {msg.subject}, Message:{msg.body}'
    except Exception as ex:
        raise ex
    
def send_invoice_admin(order_id):
    from .models import Order
    try:
        order = Order.objects.select_related('user', 'contact').prefetch_related(
            'ordered_items__product_info__product',
            'ordered_items__product_info__shop'
        ).get(id=order_id)
        
        user = order.user
        
        total_sum = sum(item.quantity * item.product_info.price for item in order.ordered_items.all())
        
        invoice_text = f"""
Накладная для исполнения заказа:

Заказ №: {order.id}
Статус: {order.get_status_display()}
Дата: {order.dt.strftime('%d.%m.%Y %H:%M')}

Информация о клиенте:

Клиент: {user.first_name} {user.last_name}
Email: {user.email}
Телефон: {order.contact.phone if order.contact else 'Не указан'}
Компания: {user.company or 'Не указана'}

Состав заказа:
"""


        for i, item in enumerate(order.ordered_items.all(), 1):
            invoice_text += f"""
{i}. {item.product_info.product.name} 
   Магазин: {item.product_info.shop.name}
   Количество: {item.quantity} шт.
   Цена: {item.product_info.price} руб.
   Сумма: {item.quantity * item.product_info.price} руб.
"""

        invoice_text += f"""
Общая сумма: {total_sum} руб.

Адрес доставки:
"""

        if order.contact:
            invoice_text += f"{order.contact.get_full_address()}"
        else:
            invoice_text += "АДРЕС ДОСТАВКИ НЕ УКАЗАН"

        invoice_text += f"""

Требуется исполнение:

1. Подтверждение наличия товара
2. Согласовать сроки доставки с клиентом
3. Организовать доставку
4. Подготовить документы
5. Подготовить счёт для оплаты

Контакты клиента:

Телефон: {order.contact.phone if order.contact else 'Требуется уточнить'}
Email: {user.email}

"""

        admin_email = getattr(settings, 'ADMIN_EMAIL', 'olegzdanov87@gmail.com')
        
        result = send_email(
            title=f'Накладная для исполнения - Заказ #{order.id}',
            message=invoice_text,
            email=admin_email
        )
        
        return f"Накладная для исполнения отправлена администратору для заказа {order.id}"
    
    except Exception as ex:
        return f"Ошибка отправки накладной: {str(ex)}"
from project.celery import Celery
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from .models import Order
from celery import shared_task
from celery import shared_task
import sentry_sdk

# Функция отправки писем
@shared_task
def send_email(title, message, email, *args, **kwargs):
    email_list = list()
    email_list.append(email)
    try:
        msg = EmailMultiAlternatives(subject=title, body=message, from_email=settings.EMAIL_HOST_USER, to=email_list)
        msg.send()
        return f'{title}: {msg.subject}, Message:{msg.body}'
    except Exception as ex:
        sentry_sdk.capture_exception(ex)
        raise ex


# Подтверждение заказа покупателю    
@shared_task
def send_order_confirmation(order_id):
    try:
        order = Order.objects.get(id=order_id)
        user = order.user
        
        subject = f"Подтверждение заказа: {order.id}"
        message = f"""
        {user.first_name or 'пользователь'}
        Ваш заказ # {order.id} успешно оформлен
        Статус: {order.get_status_display()}
        Дата: {order.dt.strftime('%d.%m.%y %H:%M')}
        """

        send_mail(subject=subject,
                  message=message,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[user.email],
        )
        return f"Order confirmation sent for order #{order_id}"
    except Order.DoesNotExist:
        sentry_sdk.capture_message(f"Order #{order_id} not found")
        return f"Order #{order_id} not found"
    except Exception as ex:
        sentry_sdk.capture_exception(ex)
        return f"Failed to send order confirmation: {str(ex)}"
    
    
# Накладная администратору
@shared_task
def send_invoice_admin(order_id):
    try:
        order = Order.objects.get(id=order_id)
        
        subject = f"Новая накладная для заказа #{order.id}"
        message = f"""
        Новая накладная создана:
        
        Заказ: #{order.id}
        Пользователь: {order.user.email}
        Дата: {order.dt.strftime('%d.%m.%Y %H:%M')}
        Статус: {order.get_status_display()}
        """
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
        )
        return f"Invoice sent to admin for order #{order_id}"
    except Exception as ex:
        sentry_sdk.capture_exception(ex)
        return f"Failed to send invoice: {str(ex)}"
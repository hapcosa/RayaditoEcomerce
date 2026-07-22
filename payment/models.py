from django.db import models
from django.utils import timezone
from orders.models import Order
# Create your models here.

class Payments(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        APPROVED = 'approved', 'Aprobado'
        REJECTED = 'rejected', 'Rechazado'
        CANCELLED = 'cancelled', 'Cancelado'
        REFUNDED = 'refunded', 'Reembolsado'
        CHARGED_BACK = 'charged_back', 'Contracargo'
        UNKNOWN = 'unknown', 'Desconocido'

    payment_id = models.BigIntegerField(unique=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, unique=True)
    status = models.CharField(
        max_length=30, choices=PaymentStatus.choices, default=PaymentStatus.PENDING,
    )
    status_detail = models.CharField(max_length=255, blank=True, default='')
    external_reference = models.CharField(max_length=255, blank=True, default='')
    payment_method_id = models.CharField(max_length=100, blank=True, default='')
    typepayment = models.CharField(max_length=255, null=True, blank=True)
    cuotas= models.BooleanField(default=False)
    stock_deducted = models.BooleanField(default=False)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    def __str__(self):
        return str(self.payment_id) + " order:" + str(self.order)
    

    

from django.db import models

class Shipping(models.Model):
    class Meta:
        verbose_name = 'Shipping'
        verbose_name_plural = 'Shipping'

    name = models.CharField(max_length=255, unique=True)
    time_to_delivery = models.CharField(max_length=255)
    description = models.TextField(max_length=1000)
    photo = models.ImageField(upload_to='logos/%y/%m')
    def __str__(self):
        return self.name

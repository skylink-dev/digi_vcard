from django.db import models
from django.core import signing
from django.urls import reverse
import qrcode
from io import BytesIO
from django.core.files import File
from colorfield.fields import ColorField
class VisitingCard(models.Model):
    name = models.CharField(max_length=100, default="John Doe", blank=True)
    designation = models.CharField(max_length=100, default="Sales Executive", blank=True)
    company_name = models.CharField(max_length=100, default="My Company", blank=True)
    phone = models.CharField(max_length=20, default="+91 0000000000", blank=True)
    whatsapp_number = models.CharField(max_length=20, default="+91 0000000000", blank=True)
    email = models.EmailField(default="example@example.com", blank=True)
    website = models.URLField(default="https://www.example.com", blank=True)
    address = models.TextField(default="123, Sample Street, City", blank=True)

    profile_image = models.ImageField(upload_to='profile_images/', default='profile_images/default.png', blank=True)
    logo = models.ImageField(upload_to='company_logos/', default='company_logos/default.png', blank=True)
    qr_center_color = ColorField(default='#000000', verbose_name="QR Center Color")
    qr_edge_color = ColorField(default='#0000FF', verbose_name="QR Edge Color")
    facebook_link = models.URLField(default="#", blank=True)
    instagram_link = models.URLField(default="#", blank=True)
    linkedin_link = models.URLField(default="#", blank=True)

    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.company_name}"

    @property
    def signed_url(self):
        signed_id = signing.dumps(self.id)
        return reverse('card_profile_signed', args=[signed_id])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save first to ensure ID is present

        qr_data = f"{self.get_full_qr_url()}"
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        filename = f'qrcode_{self.pk}.png'
        self.qr_code.save(filename, File(buffer), save=False)
        super().save(update_fields=['qr_code'])

    def get_full_qr_url(self):
        from django.contrib.sites.models import Site
        domain = Site.objects.get_current().domain
        return f"https://{domain}{self.signed_url}"

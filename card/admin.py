from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.core import signing
from django.contrib.sites.models import Site
import qrcode
from io import BytesIO
import base64
from PIL import Image, ImageEnhance, ImageDraw

from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from .models import VisitingCard
from qrcode.image.styles.moduledrawers import CircleModuleDrawer

def encrypt_id(card_id):
    """Encrypts an ID for use in a URL."""
    return signing.dumps(card_id)


@admin.register(VisitingCard)
class VisitingCardAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_name', 'phone')
    # The 'qr_code_with_face' method will be displayed as a read-only field.
    readonly_fields = ('qr_code_with_face',)

    def qr_code_with_face(self, obj):
        """
        Generates a QR code by overlaying semi-transparent dots
        on top of the user's profile image.
        """
        if not obj.id:
            return "Save the card first to generate the QR code."

        # --- 1. Dynamic URL Generation ---
        try:
            current_site = Site.objects.get_current()
            domain = current_site.domain
        except Exception:
            domain = 'localhost:8000'

        signed_id = encrypt_id(obj.id)
        url_path = reverse('card_profile_signed', args=[signed_id])

        # This will give you URL like: domain/path
        full_url = f"{domain}{url_path}"


        # --- 2. Generate the QR Code Layer ---
        # The QR code will have light red dots on a transparent background.
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=15,
            border=4,
        )
        qr.add_data(full_url)
        qr.make(fit=True)

        # Note the 'transparent' background color
        qr_img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=CircleModuleDrawer(),
            fill_color="#000000",  # Light Red
            back_color="transparent"
        ).convert('RGBA')

        # --- 3. Prepare the Background Face Image ---
        try:
            # Open face image and ensure it's in RGBA mode
            face_img = Image.open(obj.profile_image.path).convert('RGBA')
        except (ValueError, FileNotFoundError):
            return "Profile image not found. Please upload one."

        # Resize the face image to be the same size as the QR code
        face_img = face_img.resize(qr_img.size, Image.Resampling.LANCZOS)

        # --- 4. Adjust QR Code Opacity ---
        # Get the alpha (transparency) channel of the QR code
        qr_alpha = qr_img.split()[2]

        # Enhance the alpha channel to make the dots semi-transparent.
        # A factor of 0.7 makes the dots 70% opaque. Lower numbers make them more transparent.
        qr_alpha = ImageEnhance.Brightness(qr_alpha).enhance(0.8)
        
        # Put the modified alpha channel back into the QR image
        qr_img.putalpha(qr_alpha)

        # --- 5. Combine the Face and QR Code ---
        # Paste the semi-transparent QR code directly onto the face image
        combined_img = Image.alpha_composite(face_img, qr_img)
        
        # --- 6. Add a Final White Border (Optional, but looks nice) ---
        border_size = 15
        bordered_img = Image.new(
            'RGBA',
            (combined_img.width + border_size * 2, combined_img.height + border_size * 2),
            (255, 25, 25, 25)
        )
        bordered_img.paste(combined_img, (border_size, border_size))


        # --- 7. Convert to Base64 for Admin Preview ---
        buffer = BytesIO()
        bordered_img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return mark_safe(f'<img src="data:image/png;base64,{img_str}" width="300" /><br><small>{full_url}</small>')


    # Set a user-friendly name for the field in the Django admin
    qr_code_with_face.short_description = "QR Code Preview"
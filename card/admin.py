from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.core import signing
from django.contrib.sites.models import Site

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask

from io import BytesIO
import base64
from PIL import Image, ImageColor

from .models import VisitingCard


def encrypt_id(card_id):
    return signing.dumps(card_id)


@admin.register(VisitingCard)
class VisitingCardAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_name', 'phone')
    readonly_fields = ('qr_code_preview_with_download',)
    fields = (
        'name', 'designation','company_name', 'phone', 'whatsapp_number','email', 'website', 'address',
        'profile_image', 'logo',
        'qr_center_color', 'qr_edge_color',
        'qr_code_preview_with_download',
    )

    def qr_code_preview_with_download(self, obj):
        if not obj.id:
            return "Save the card first to generate the QR code."

        try:
            current_site = Site.objects.get_current()
            domain = current_site.domain
        except Exception:
            domain = 'localhost:8000'

        signed_id = encrypt_id(obj.id)
        url_path = reverse('card_profile_signed', args=[signed_id])
        full_url = f"https://{domain}{url_path}"

        # ✅ Convert Hex Color to RGB tuple
        center_rgb = ImageColor.getrgb(obj.qr_center_color or "#000000")
        edge_rgb = ImageColor.getrgb(obj.qr_edge_color or "#0000FF")

        # 1️⃣ Generate Styled QR Code with Selected Colors
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(full_url)
        qr.make(fit=True)

        qr_img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=RadialGradiantColorMask(
                back_color=(255, 255, 255),
                center_color=center_rgb,
                edge_color=edge_rgb
            )
        ).convert('RGBA')

        # 2️⃣ Add Logo at Top-Left
        try:
            logo_img = Image.open(obj.logo.path).convert('RGBA')
            logo_size = (int(qr_img.size[0] * 0.15), int(qr_img.size[1] * 0.15))
            logo_img = logo_img.resize(logo_size, Image.Resampling.LANCZOS)
            qr_img.paste(logo_img, (10, 10), mask=logo_img)
        except Exception:
            pass

        # 3️⃣ Add Profile at Center
        try:
            profile_img = Image.open(obj.profile_image.path).convert('RGBA')
            profile_size = (int(qr_img.size[0] * 0.30), int(qr_img.size[1] * 0.30))
            profile_img = profile_img.resize(profile_size, Image.Resampling.LANCZOS)
            pos = ((qr_img.size[0] - profile_img.size[0]) // 2, (qr_img.size[1] - profile_img.size[1]) // 2)
            qr_img.paste(profile_img, pos, mask=profile_img)
        except Exception:
            pass

        # 4️⃣ Save in different formats
        formats = {'PNG': 'png', 'JPEG': 'jpeg', 'WEBP': 'webp'}
        download_links = ""
        for name, fmt in formats.items():
            buffer = BytesIO()
            converted_img = qr_img.convert('RGB') if fmt == 'jpeg' else qr_img
            converted_img.save(buffer, format=fmt.upper())
            img_data = base64.b64encode(buffer.getvalue()).decode()
            download_links += f'<a download="qr_code.{fmt}" href="data:image/{fmt};base64,{img_data}">Download {name}</a><br>'

        # 5️⃣ Show in Admin
        preview_buffer = BytesIO()
        qr_img.save(preview_buffer, format="PNG")
        preview_data = base64.b64encode(preview_buffer.getvalue()).decode()

        return mark_safe(f'''
            <img src="data:image/png;base64,{preview_data}" width="300"/><br>
            <small>{full_url}</small><br><br>
            {download_links}
        ''')

    qr_code_preview_with_download.short_description = "Styled QR with Download Options"

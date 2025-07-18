from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.core import signing

from .models import VisitingCard
from PIL import Image, ImageDraw, ImageFont

from io import BytesIO

def card_profile(request, card_id):
    """
    Display card based on the plain ID (Direct URL).
    """
    card = get_object_or_404(VisitingCard, id=card_id)
    return render(request, 'card/show_card.html', {'card': card})


def download_vcard(request, card_id):
    """
    Download VCF file with contact details.
    """
    card = get_object_or_404(VisitingCard, id=card_id)
    vcard_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{card.name}
ORG:{card.company_name}
TITLE:{card.designation}
TEL;TYPE=work,voice:{card.phone}
EMAIL;TYPE=internet:{card.email}
URL:{card.website}
ADR;TYPE=work:;;{card.address}
END:VCARD
"""
    response = HttpResponse(vcard_content, content_type='text/vcard')
    response['Content-Disposition'] = f'attachment; filename="{card.name}.vcf"'
    return response


def card_profile_signed(request, signed_id):
    try:
        card_id = signing.loads(signed_id)
        card = get_object_or_404(VisitingCard, id=card_id)
    except signing.BadSignature:
        raise Http404("Invalid QR Code link.")
    return render(request, 'card/show_card.html', {'card': card})


def download_card_image(request, card_id):
    card = get_object_or_404(VisitingCard, id=card_id)

    # Create blank white image
    img = Image.new('RGB', (600, 350), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Optional: Load a font
    try:
        font = ImageFont.truetype('arial.ttf', size=20)
    except:
        font = ImageFont.load_default()

    # Draw Card Details
    draw.text((20, 20), f"Name: {card.name}", fill='black', font=font)
    draw.text((20, 60), f"Designation: {card.designation}", fill='black', font=font)
    draw.text((20, 100), f"Company: {card.company_name}", fill='black', font=font)
    draw.text((20, 140), f"Phone: {card.phone}", fill='black', font=font)
    draw.text((20, 180), f"Email: {card.email}", fill='black', font=font)
    draw.text((20, 220), f"Website: {card.website}", fill='black', font=font)
    draw.text((20, 260), f"Address: {card.address}", fill='black', font=font)

    # Save image to buffer
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    # Send as response
    response = HttpResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename={card.name}_visiting_card.png'
    return response

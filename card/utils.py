from django.core import signing

def encrypt_id(card_id):
    return signing.dumps(card_id)

def decrypt_id(signed_id):
    try:
        return signing.loads(signed_id)
    except signing.BadSignature:
        return None

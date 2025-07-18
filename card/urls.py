from django.urls import path
from . import views

urlpatterns = [
    path('card/id/<int:card_id>/', views.card_profile, name='card_profile'),
    path('card/<str:signed_id>/', views.card_profile_signed, name='card_profile_signed'),
    path('download/<int:card_id>/', views.download_vcard, name='download_vcard'),
    path('download-card-image/<int:card_id>/', views.download_card_image, name='download_card_image'),
]

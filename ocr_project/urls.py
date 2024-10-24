from django.urls import path
from .views import ocr_image

urlpatterns = [
    path('ocr/', ocr_image, name='ocr_image'),
]

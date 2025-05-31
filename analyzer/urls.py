from django.urls import path
from . import views

urlpatterns = [
    path('upload-apk/', views.upload_apk, name='upload_apk'),
    path('analyze-playstore-link/', views.analyze_playstore_link, name='analyze_playstore_link'),
    path('my-url/', views.my_view, name='my_view'),
]

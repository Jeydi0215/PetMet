from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

def map_view(request):
    return render(request, 'map.html')

urlpatterns = [
    path('', include('LoginPage.urls')),
    path('admin/', admin.site.urls),
    path('map/', map_view, name='map'),
    path('adoption/', include('adoption.urls')),  # ADD THIS LINE
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
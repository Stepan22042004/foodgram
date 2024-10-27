from django.contrib import admin
from django.urls import path, include

from foodgram.views import url

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<slug:short>/', url)
]

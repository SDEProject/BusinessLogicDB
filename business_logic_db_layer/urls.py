from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers

from business_logic_db_layer import views
from travelando import settings

router = routers.SimpleRouter()


schema_view = get_schema_view(
   openapi.Info(
      title="Business logic DB API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', include(router.urls)),
    path(r'result/', views.ResultView.as_view(), name='result'),
    path(r'search/', views.SearchView.as_view(), name='search'),
    path(r'delete/', views.DeleteView.as_view(), name='delete'),

    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui')
]

"""travelando URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from travelando import settings

urlpatterns = [] + static(settings.STATIC_URL)

if settings.DEBUG:
    urlpatterns.append(path('admin/', admin.site.urls))

if settings.SERVICE_NAME == settings.SERVICE_MYDB_DATA_LAYER:
    urlpatterns.append(path(settings.SERVICE_MYDB_DATA_LAYER+'/', include('mydb_data_layer.urls')))

if settings.SERVICE_NAME == settings.SERVICE_MYDB_ADAPTER_LAYER:
    urlpatterns.append(path(settings.SERVICE_MYDB_ADAPTER_LAYER+'/', include('mydb_adapter_layer.urls')))

if settings.SERVICE_NAME == settings.SERVICE_CHOREOGRAPHER:
    urlpatterns.append(path(settings.SERVICE_CHOREOGRAPHER+'/', include('choreographer.urls')))

if settings.SERVICE_NAME == settings.SERVICE_BUSINESS_LOGIC:
    urlpatterns.append(path(settings.SERVICE_BUSINESS_LOGIC+'/', include('business_logic.urls')))

if settings.SERVICE_NAME == settings.SERVICE_PROCESS_CENTRIC:
    urlpatterns.append(path(settings.SERVICE_PROCESS_CENTRIC+'/', include('process_centric_layer.urls')))

if settings.SERVICE_NAME == settings.SERVICE_KNOWLEDGE:
    urlpatterns.append(path(settings.SERVICE_KNOWLEDGE+'/', include('knowledge_graph_data_layer.urls')))

if settings.SERVICE_NAME == settings.SERVICE_PROCESS_CENTRIC_DB:
    urlpatterns.append(path(settings.SERVICE_PROCESS_CENTRIC_DB+'/', include('process_centric_db_layer.urls')))

if settings.SERVICE_NAME == settings.SERVICE_BUSINESS_LOGIC_DB:
    urlpatterns.append(path(settings.SERVICE_BUSINESS_LOGIC_DB+'/', include('business_logic_db_layer.urls')))

if settings.SERVICE_NAME == settings.SERVICE_QUERY_SELECTION:
    urlpatterns.append(path(settings.SERVICE_QUERY_SELECTION+'/', include('query_selection_service.urls')))

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from .api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls, name='api')
]


# if settings.DEBUG:
#     try:
#         import debug_toolbar
#
#         urlpatterns += [
#             path('__debug__/', include(debug_toolbar.urls)),
#         ]
#     except ImportError:
#         pass
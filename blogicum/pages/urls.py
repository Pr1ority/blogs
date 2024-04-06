from . import views
from django.urls import path




app_name = 'pages'
urlpatterns = [
    path('about/', views.AboutPage.as_view(), name='about'),
    path('rules/', views.RulesPage.as_view(), name='rules'),
]


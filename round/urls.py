from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_rounds, name='list-rounds'),
    path('draw/', views.ladder_draw, name='ladder-draw'),
]
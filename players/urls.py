from django.urls import path
from . import views

urlpatterns = [
    path('player/<int:player_id>', views.edit_player, name='edit-player'),
    path('create/', views.create_player, name='create-player'),
    path('', views.list_players, name='list-players'),

]

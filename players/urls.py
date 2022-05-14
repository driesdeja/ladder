"""
Path to view mapping for the players module
"""
from django.urls import path
from . import views

urlpatterns = [
    path('player/<int:player_id>', views.edit_player, name='edit-player'),
    path('administration/create/', views.create_player, name='create-player'),
    path('administration/reset-ranking/', views.reset_rankings, name='reset-rankings'),
    path('administration/import-players', views.import_players, name='import-players'),
    path('administration/export-players', views.export_players, name='export-players'),
    path('administration/download-player-list', views.download_players, name='download-players'),
    path('players/', views.list_players, name='list-players'),
    path('', views.list_players, name='list-players'),

]

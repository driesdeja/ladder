from django.urls import path
from . import views

urlpatterns = [
    path('', views.ladder_admin, name='ladder-admin'),
    path('draw/', views.ladder_draw, name='ladder-draw'),
    path('ladder/', views.ladder_admin, name='ladder-admin'),
    path('ladder/<int:ladder_id>', views.ladder_detail, name='ladder-detail'),
    path('ladder/round/<int:round_id>', views.round_detail, name='round-detail'),
    path('ladder/round/add-players', views.manage_players_in_round, name='manage-players-in-round'),
    path('ladder/round/add-players-to-round', views.add_players_to_round, name='add-players-to-round'),
    path('ladder/round/<int:round_id>/draw', views.round_draw, name='round-draw'),
    path('ladder/round/<int:round_id>/matches', views.close_draw, name='close-draw'),
    path('ladder/round/<int:round_id>/results', views.capture_results, name='capture-results')

]

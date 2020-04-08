from django.urls import path
from . import views

urlpatterns = [
    path('', views.ladder_overview, name='ladder-overview'),
    path('draw/', views.ladder_draw, name='ladder-draw'),
    path('administration/ladder/', views.ladder_admin, name='ladder-admin'),
    path('administration/ladder/<int:ladder_id>', views.ladder_detail, name='ladder-detail'),
    path('administration/ladder/<int:ladder_id>/create-round', views.create_ladder_round, name='create-ladder-round'),
    path('ladder/round/<int:round_id>', views.round_detail, name='round-detail'),
    path('administration/ladder/round/<int:round_id>/add-players', views.manage_players_in_round,
         name='manage-players-in-round'),
    path('administration/ladder/round/<int:round_id>/add-players-to-round', views.add_players_to_round,
         name='add-players-to-round'),
    path('administration/ladder/round/<int:round_id>/draw', views.round_draw, name='round-draw'),
    path('administration/ladder/round/<int:round_id>/close-draw', views.close_draw, name='close-draw'),
    path('administration/ladder/round/<int:round_id>/capture', views.capture_results, name='capture-results'),
    path('administration/ladder/round/<int:round_id>', views.admin_round_detail, name='admin-round-detail'),
    path('ladder/round/<int:round_id>/results', views.view_round_results, name='view-results'),
    path('ladder/round/<int:round_id>/match/<int:match_id>', views.edit_match, name='edit-match'),
    path('administration/ladder/round/<int:round_id>/ranking_updates', views.update_players_ranking,
         name='update-ranking'),
    path('administration/ladder/round/<int:round_id>/schedule-matches', views.schedule_matches,
         name='schedule-matches'),
    path('administration/ladder/round/<int:round_id>/setup-scheduling', views.setup_scheduling_for_round,
         name='setup-scheduling'),
    path('administration/ladder/round/<int:round_id>/save-scheduled-match', views.save_scheduled_match_view, name='save-scheduled-match'),
    path('player/<int:player_id>', views.player_profile, name='player-profile')
]

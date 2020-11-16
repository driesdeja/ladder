ACTIVE_PLAYERS_SQL = """
        select 
        players_player.*
    from 
        players_player,
        players_active
    where
        players_player.id = players_active.player_id
        and 
        players_active.eff_to_date is null
        """

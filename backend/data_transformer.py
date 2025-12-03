"""
Data Transformer Module for NCAAFB Data Pipeline.

This module handles parsing, flattening, and normalizing JSON responses
into SQL-ready tabular format.
"""

import os
import sys
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.utils.helpers import (
        safe_get, normalize_string, normalize_int, normalize_float, 
        normalize_date, save_json_file, get_project_root, ensure_dir,
        normalize_uuid, convert_height_to_inches
    )
except ImportError:
    from utils.helpers import (
        safe_get, normalize_string, normalize_int, normalize_float, 
        normalize_date, save_json_file, get_project_root, ensure_dir,
        normalize_uuid, convert_height_to_inches
    )

import uuid


class DataTransformer:
    """Transforms raw JSON API responses into normalized data structures."""
    
    def __init__(self):
        """Initialize the data transformer."""
        self.clean_data_dir = os.path.join(get_project_root(), 'backend', 'clean_data')
        ensure_dir(self.clean_data_dir)
        
        # Data storage
        self.conferences = []
        self.divisions = []
        self.venues = []
        self.teams = []
        self.seasons = []
        self.players = []
        self.player_statistics = []
        self.rankings = []
        self.coaches = []
        
        # ID mappings for relationships (using UUIDs from API)
        self.conference_id_map = {}  # api_id -> uuid
        self.division_id_map = {}    # (conference_id, name) -> uuid
        self.venue_id_map = {}       # api_id -> uuid
        self.team_id_map = {}        # api_id -> uuid (use API UUID directly)
        self.season_id_map = {}      # (year, type) -> uuid
        self.player_id_map = {}      # api_id -> uuid (use API UUID directly)
        
    def transform_hierarchy(self, hierarchy_data: Dict[str, Any]) -> None:
        """
        Transform league hierarchy data into conferences and divisions.
        
        Args:
            hierarchy_data: Raw hierarchy JSON data
        """
        if not hierarchy_data:
            return
            
        conferences_list = safe_get(hierarchy_data, 'conferences', default=[])
        if not conferences_list:
            return
        
        conference_id = 1
        division_id = 1
        
        for conf in conferences_list:
            conf_name = normalize_string(safe_get(conf, 'name'))
            conf_alias = normalize_string(safe_get(conf, 'alias'))
            
            if conf_name:
                self.conference_id_map[conf_name] = conference_id
                
                self.conferences.append({
                    'conference_id': conference_id,
                    'name': conf_name,
                    'alias': conf_alias
                })
                
                # Process divisions
                divisions_list = safe_get(conf, 'divisions', default=[])
                for div in divisions_list:
                    div_name = normalize_string(safe_get(div, 'name'))
                    if div_name:
                        self.division_id_map[f"{conf_name}_{div_name}"] = division_id
                        division_id += 1
                
                conference_id += 1
    
    def transform_venues(self, teams_data: Dict[str, Any]) -> None:
        """
        Extract and transform venue data from teams.
        
        Args:
            teams_data: Raw teams JSON data
        """
        if not teams_data:
            return
            
        teams_list = safe_get(teams_data, 'teams', default=[])
        venue_id = 1
        
        for team in teams_list:
            venue = safe_get(team, 'venue')
            if venue:
                venue_name = normalize_string(safe_get(venue, 'name'))
                if venue_name and venue_name not in self.venue_id_map:
                    self.venue_id_map[venue_name] = venue_id
                    
                    self.venues.append({
                        'venue_id': venue_id,
                        'name': venue_name,
                        'city': normalize_string(safe_get(venue, 'city')),
                        'state': normalize_string(safe_get(venue, 'state')),
                        'country': normalize_string(safe_get(venue, 'country', default='USA')),
                        'zip': normalize_string(safe_get(venue, 'zip')),
                        'address': normalize_string(safe_get(venue, 'address')),
                        'capacity': normalize_int(safe_get(venue, 'capacity')),
                        'surface': normalize_string(safe_get(venue, 'surface')),
                        'roof_type': normalize_string(safe_get(venue, 'roof_type')),
                        'latitude': normalize_float(safe_get(venue, 'location', 'latitude')),
                        'longitude': normalize_float(safe_get(venue, 'location', 'longitude'))
                    })
                    
                    venue_id += 1
    
    def transform_teams(self, teams_data: Dict[str, Any], hierarchy_data: Dict[str, Any] = None) -> None:
        """
        Transform teams data.
        
        Args:
            teams_data: Raw teams JSON data
            hierarchy_data: Optional hierarchy data for conference/division mapping
        """
        if not teams_data:
            return
            
        teams_list = safe_get(teams_data, 'teams', default=[])
        team_id = 1
        
        for team in teams_list:
            api_team_id = safe_get(team, 'id')
            if not api_team_id:
                continue
                
            self.team_id_map[api_team_id] = team_id
            
            # Get conference and division
            conference_name = normalize_string(safe_get(team, 'conference', 'name'))
            division_name = normalize_string(safe_get(team, 'division', 'name'))
            
            conference_id = self.conference_id_map.get(conference_name) if conference_name else None
            division_id = None
            if conference_name and division_name:
                division_key = f"{conference_name}_{division_name}"
                division_id = self.division_id_map.get(division_key)
            
            # Get venue
            venue_name = normalize_string(safe_get(team, 'venue', 'name'))
            venue_id = self.venue_id_map.get(venue_name) if venue_name else None
            
            self.teams.append({
                'team_id': team_id,
                'market': normalize_string(safe_get(team, 'market')),
                'name': normalize_string(safe_get(team, 'name')),
                'alias': normalize_string(safe_get(team, 'alias')),
                'founded': normalize_int(safe_get(team, 'founded')),
                'mascot': normalize_string(safe_get(team, 'mascot')),
                'fight_song': normalize_string(safe_get(team, 'fight_song')),
                'championships_won': normalize_int(safe_get(team, 'championships_won', default=0)),
                'conference_id': conference_id,
                'division_id': division_id,
                'venue_id': venue_id
            })
            
            team_id += 1
    
    def transform_seasons(self, seasons_data: Dict[str, Any]) -> None:
        """
        Transform seasons data.
        
        Args:
            seasons_data: Raw seasons JSON data
        """
        if not seasons_data:
            return
            
        seasons_list = safe_get(seasons_data, 'seasons', default=[])
        season_id = 1
        
        for season in seasons_list:
            year = normalize_int(safe_get(season, 'year'))
            type_code = normalize_string(safe_get(season, 'type', 'code'))
            
            if year and type_code:
                key = (year, type_code)
                if key not in self.season_id_map:
                    self.season_id_map[key] = season_id
                    
                    self.seasons.append({
                        'season_id': season_id,
                        'year': year,
                        'start_date': normalize_date(safe_get(season, 'start_date')),
                        'end_date': normalize_date(safe_get(season, 'end_date')),
                        'status': normalize_string(safe_get(season, 'status')),
                        'type_code': type_code
                    })
                    
                    season_id += 1
    
    def transform_players(self, rosters_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Transform player data from rosters.
        
        Args:
            rosters_data: Dictionary of team_id -> roster data
        """
        if not rosters_data:
            return
            
        player_id = 1
        
        for team_api_id, roster_data in rosters_data.items():
            team_db_id = self.team_id_map.get(team_api_id)
            if not team_db_id:
                continue
            
            players_list = safe_get(roster_data, 'players', default=[])
            
            for player in players_list:
                api_player_id = safe_get(player, 'id')
                if not api_player_id:
                    continue
                
                # Get name information - API has both direct fields and nested name object
                last_name = normalize_string(safe_get(player, 'last_name')) or normalize_string(safe_get(player, 'name', 'last'))
                first_name = normalize_string(safe_get(player, 'first_name')) or normalize_string(safe_get(player, 'name', 'first'))
                
                # If still no last_name, try extracting from full name
                if not last_name:
                    full_name = normalize_string(safe_get(player, 'name'))  # Could be string or dict
                    if isinstance(full_name, str):
                        name_parts = full_name.strip().split()
                        if len(name_parts) > 0:
                            last_name = name_parts[-1]
                            if not first_name and len(name_parts) > 1:
                                first_name = ' '.join(name_parts[:-1])
                    elif isinstance(full_name, dict):
                        last_name = normalize_string(safe_get(full_name, 'last'))
                        first_name = normalize_string(safe_get(full_name, 'first')) or first_name
                
                # Skip if still no last_name (but allow null for flexibility)
                if not last_name:
                    last_name = "Unknown"  # Use placeholder instead of skipping
                
                if api_player_id not in self.player_id_map:
                    self.player_id_map[api_player_id] = player_id
                    
                    # Get position - could be string or object
                    position = safe_get(player, 'position')
                    if isinstance(position, dict):
                        position = safe_get(position, 'name') or safe_get(position, 'abbr')
                    position = normalize_string(position)
                    
                    self.players.append({
                        'player_id': player_id,
                        'first_name': first_name,
                        'last_name': last_name,
                        'abbr_name': normalize_string(safe_get(player, 'abbr_name')) or normalize_string(safe_get(player, 'name', 'abbr')),
                        'birth_place': normalize_string(safe_get(player, 'birth_place')),
                        'position': position,
                        'height': normalize_string(safe_get(player, 'height')),
                        'weight': normalize_int(safe_get(player, 'weight')),
                        'status': normalize_string(safe_get(player, 'status')),
                        'eligibility': normalize_string(safe_get(player, 'eligibility')),
                        'team_id': team_db_id
                    })
                    
                    player_id += 1
    
    def transform_coaches(self, rosters_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Transform coach data from rosters.
        
        Args:
            rosters_data: Dictionary of team_id -> roster data
        """
        if not rosters_data:
            return
            
        coach_id = 1
        
        for team_api_id, roster_data in rosters_data.items():
            team_db_id = self.team_id_map.get(team_api_id)
            if not team_db_id:
                continue
            
            coaches_list = safe_get(roster_data, 'coaches', default=[])
            
            for coach in coaches_list:
                name_data = safe_get(coach, 'name', default={})
                full_name = normalize_string(safe_get(name_data, 'full'))
                
                if full_name:
                    self.coaches.append({
                        'coach_id': coach_id,
                        'full_name': full_name,
                        'position': normalize_string(safe_get(coach, 'position')),
                        'team_id': team_db_id
                    })
                    
                    coach_id += 1
    
    def transform_player_statistics(self, season_stats_data: Dict[str, Dict[str, Any]], 
                                   year: int = 2025, season_type: str = "REG") -> None:
        """
        Transform player statistics data.
        
        Args:
            season_stats_data: Dictionary of team_id -> statistics data
            year: Season year
            season_type: Season type
        """
        if not season_stats_data:
            return
            
        season_key = (year, season_type)
        season_db_id = self.season_id_map.get(season_key)
        if not season_db_id:
            return
        
        stat_id = 1
        
        for team_api_id, stats_data in season_stats_data.items():
            team_db_id = self.team_id_map.get(team_api_id)
            if not team_db_id:
                continue
            
            players_stats = safe_get(stats_data, 'players', default=[])
            
            for player_stat in players_stats:
                api_player_id = safe_get(player_stat, 'id')
                if not api_player_id:
                    continue
                
                player_db_id = self.player_id_map.get(api_player_id)
                if not player_db_id:
                    # Skip statistics for players that weren't inserted
                    continue
                
                # Extract statistics
                stats = safe_get(player_stat, 'statistics', default={})
                
                self.player_statistics.append({
                    'stat_id': stat_id,
                    'player_id': player_db_id,
                    'team_id': team_db_id,
                    'season_id': season_db_id,
                    'games_played': normalize_int(safe_get(stats, 'games_played')),
                    'games_started': normalize_int(safe_get(stats, 'games_started')),
                    'rushing_yards': normalize_int(safe_get(stats, 'rushing', 'yards')),
                    'rushing_touchdowns': normalize_int(safe_get(stats, 'rushing', 'touchdowns')),
                    'receiving_yards': normalize_int(safe_get(stats, 'receiving', 'yards')),
                    'receiving_touchdowns': normalize_int(safe_get(stats, 'receiving', 'touchdowns')),
                    'kick_return_yards': normalize_int(safe_get(stats, 'kick_returns', 'yards')),
                    'fumbles': normalize_int(safe_get(stats, 'fumbles', 'total'))
                })
                
                stat_id += 1
    
    def transform_rankings(self, rankings_data: Dict[str, Any], 
                          rankings_type: str = "current", year: int = 2025, week: int = None) -> None:
        """
        Transform rankings data.
        
        Args:
            rankings_data: Raw rankings JSON data
            rankings_type: Type of rankings ('current' or 'week')
            year: Season year
            week: Week number (if rankings_type is 'week')
        """
        if not rankings_data:
            return
        
        poll_id = normalize_string(safe_get(rankings_data, 'poll', 'id'))
        poll_name = normalize_string(safe_get(rankings_data, 'poll', 'name'))
        
        # Extract week from the response if not provided
        if week is None:
            week = normalize_int(safe_get(rankings_data, 'week'))
        
        season_key = (year, "REG")
        season_db_id = self.season_id_map.get(season_key)
        
        rankings_list = safe_get(rankings_data, 'rankings', default=[])
        ranking_id = len(self.rankings) + 1
        
        for rank_item in rankings_list:
            # The API returns team ID directly in the ranking item, not nested under 'team'
            team_api_id = safe_get(rank_item, 'id')
            if not team_api_id:
                continue
            
            team_db_id = self.team_id_map.get(team_api_id)
            if not team_db_id:
                continue
            
            self.rankings.append({
                'ranking_id': ranking_id,
                'poll_id': poll_id,
                'poll_name': poll_name,
                'season_id': season_db_id,
                'week': week if week else None,
                'effective_time': normalize_date(safe_get(rankings_data, 'effective_time')),
                'team_id': team_db_id,
                'rank': normalize_int(safe_get(rank_item, 'rank')),
                'prev_rank': normalize_int(safe_get(rank_item, 'prev_rank')),
                'points': normalize_int(safe_get(rank_item, 'points')),
                'fp_votes': normalize_int(safe_get(rank_item, 'fp_votes')),
                'wins': normalize_int(safe_get(rank_item, 'wins')),
                'losses': normalize_int(safe_get(rank_item, 'losses')),
                'ties': normalize_int(safe_get(rank_item, 'ties'))
            })
            
            ranking_id += 1

    def transform_schedule(self, schedule_data: Dict[str, Any], year: int = 2025) -> None:
        """
        Transform season schedule data into a simplified clean structure and save.
        """
        if not schedule_data:
            return

        games = []
        game_id = 1

        schedule_list = schedule_data.get('schedule') or schedule_data.get('games') or []
        for item in schedule_list:
            # Try common fields; be tolerant to structure differences
            home = item.get('home') or item.get('home_team') or {}
            away = item.get('away') or item.get('away_team') or {}
            venue = item.get('venue') or {}
            event_time = item.get('scheduled') or item.get('date') or item.get('start_time')

            home_api_id = home.get('id') if isinstance(home, dict) else None
            away_api_id = away.get('id') if isinstance(away, dict) else None
            venue_name = venue.get('name') if isinstance(venue, dict) else None

            games.append({
                'game_id': game_id,
                'home_team_api_id': home_api_id,
                'away_team_api_id': away_api_id,
                'scheduled': event_time,
                'venue_name': venue_name,
            })

            game_id += 1

        # Save schedule into clean_data
        filepath = os.path.join(self.clean_data_dir, f"season_schedule_{year}.json")
        save_json_file(games, filepath)
        print(f"Saved {len(games)} schedule entries to season_schedule_{year}.json")
    
    def transform_all_data(self, all_api_data: Dict[str, Any], year: int = 2025, 
                          season_type: str = "REG") -> Dict[str, List[Dict[str, Any]]]:
        """
        Transform all API data into normalized structures.
        
        Args:
            all_api_data: Dictionary containing all fetched API data
            year: Season year
            season_type: Season type
            
        Returns:
            Dictionary containing all transformed data tables
        """
        print("=" * 60)
        print("Starting data transformation...")
        print("=" * 60)
        
        # Transform in dependency order
        if all_api_data.get('hierarchy'):
            print("Transforming hierarchy...")
            self.transform_hierarchy(all_api_data['hierarchy'])
        
        if all_api_data.get('teams'):
            print("Transforming venues...")
            self.transform_venues(all_api_data['teams'])
            print("Transforming teams...")
            self.transform_teams(all_api_data['teams'], all_api_data.get('hierarchy'))
        
        if all_api_data.get('seasons'):
            print("Transforming seasons...")
            self.transform_seasons(all_api_data['seasons'])
        
        if all_api_data.get('rosters'):
            print("Transforming players...")
            self.transform_players(all_api_data['rosters'])
            print("Transforming coaches...")
            self.transform_coaches(all_api_data['rosters'])
        
        if all_api_data.get('season_stats'):
            print("Transforming player statistics...")
            self.transform_player_statistics(all_api_data['season_stats'], year, season_type)
        
        if all_api_data.get('rankings_current'):
            print("Transforming current rankings...")
            self.transform_rankings(all_api_data['rankings_current'], 'current', year)
        
        if all_api_data.get('rankings_week1'):
            print("Transforming week 1 rankings...")
            self.transform_rankings(all_api_data['rankings_week1'], 'week', year, week=1)

        if all_api_data.get('season_schedule'):
            print("Transforming season schedule...")
            self.transform_schedule(all_api_data['season_schedule'], year)
        
        # Compile results
        transformed_data = {
            'conferences': self.conferences,
            'venues': self.venues,
            'teams': self.teams,
            'seasons': self.seasons,
            'players': self.players,
            'player_statistics': self.player_statistics,
            'rankings': self.rankings,
            'coaches': self.coaches
        }
        
        # Save transformed data
        for table_name, data in transformed_data.items():
            filepath = os.path.join(self.clean_data_dir, f"{table_name}.json")
            save_json_file(data, filepath)
            print(f"Saved {len(data)} records to {table_name}.json")
        
        print("\n" + "=" * 60)
        print("Data transformation completed!")
        print("=" * 60)
        
        return transformed_data


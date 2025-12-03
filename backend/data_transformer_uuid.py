"""
Data Transformer Module for NCAAFB Data Pipeline - UUID Version.

This module handles parsing, flattening, and normalizing JSON responses
into SQL-ready tabular format using UUIDs as specified.
"""

import os
import sys
import uuid
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


class DataTransformer:
    """Transforms raw JSON API responses into normalized data structures with UUIDs."""
    
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
        
        # ID mappings for relationships (using UUIDs)
        self.conference_id_map = {}  # name -> uuid
        self.division_id_map = {}    # (conference_id, name) -> uuid
        self.venue_id_map = {}       # api_id or name -> uuid
        self.team_id_map = {}        # api_id -> uuid (use API UUID directly)
        self.season_id_map = {}      # (year, type) -> uuid
        self.player_id_map = {}      # api_id -> uuid (use API UUID directly)
        
    def transform_hierarchy(self, hierarchy_data: Dict[str, Any]) -> None:
        """
        Transform league hierarchy data into conferences and divisions.
        The hierarchy structure is: divisions > conferences > teams
        
        Args:
            hierarchy_data: Raw hierarchy JSON data
        """
        if not hierarchy_data:
            return
        
        # The API structure is: { divisions: [ { conferences: [ ... ] } ] }
        divisions_list = safe_get(hierarchy_data, 'divisions', default=[])
        if not divisions_list:
            return
        
        for div in divisions_list:
            div_name = normalize_string(safe_get(div, 'name'))
            div_alias = normalize_string(safe_get(div, 'alias'))
            div_api_id = normalize_uuid(safe_get(div, 'id'))
            
            if div_name:
                # Use API UUID if available, otherwise generate one
                if div_api_id:
                    div_uuid = div_api_id
                else:
                    div_uuid = str(uuid.uuid4())
                
                # Process conferences under this division
                conferences_list = safe_get(div, 'conferences', default=[])
                for conf in conferences_list:
                    conf_name = normalize_string(safe_get(conf, 'name'))
                    conf_alias = normalize_string(safe_get(conf, 'alias'))
                    conf_api_id = normalize_uuid(safe_get(conf, 'id'))
                    
                    if conf_name:
                        # Use API UUID if available, otherwise generate one
                        if conf_api_id:
                            conf_uuid = conf_api_id
                        else:
                            conf_uuid = str(uuid.uuid4())
                        
                        # Store conference mapping
                        self.conference_id_map[conf_name] = conf_uuid
                        
                        # Add conference if not already added
                        if not any(c['conference_id'] == conf_uuid for c in self.conferences):
                            self.conferences.append({
                                'conference_id': conf_uuid,
                                'name': conf_name,
                                'alias': conf_alias
                            })
                        
                        # Add division with conference link
                        division_key = (conf_uuid, div_name)
                        self.division_id_map[division_key] = div_uuid
                        
                        # Add division if not already added
                        if not any(d['division_id'] == div_uuid for d in self.divisions):
                            self.divisions.append({
                                'division_id': div_uuid,
                                'name': div_name,
                                'alias': div_alias,
                                'conference_id': conf_uuid
                            })
                        
                        # Extract venues from teams in hierarchy
                        teams_list = safe_get(conf, 'teams', default=[])
                        for team in teams_list:
                            venue = safe_get(team, 'venue')
                            if venue:
                                self._extract_venue(venue)
    
    def _extract_venue(self, venue: Dict[str, Any]) -> Optional[str]:
        """
        Extract venue information and return venue UUID.
        
        Args:
            venue: Venue data dictionary
            
        Returns:
            Venue UUID or None
        """
        if not venue:
            return None
        
        venue_api_id = normalize_uuid(safe_get(venue, 'id'))
        venue_name = normalize_string(safe_get(venue, 'name'))
        
        if venue_api_id:
            # Use API ID as primary key
            if venue_api_id not in self.venue_id_map:
                self.venue_id_map[venue_api_id] = venue_api_id
                
                # Extract lat/lng from location object
                location = safe_get(venue, 'location', default={})
                lat = normalize_float(safe_get(location, 'lat'))
                lng = normalize_float(safe_get(location, 'lng'))
                
                self.venues.append({
                    'venue_id': venue_api_id,
                    'name': venue_name,
                    'city': normalize_string(safe_get(venue, 'city')),
                    'state': normalize_string(safe_get(venue, 'state')),
                    'country': normalize_string(safe_get(venue, 'country', default='USA')),
                    'zip': normalize_string(safe_get(venue, 'zip')),
                    'address': normalize_string(safe_get(venue, 'address')),
                    'capacity': normalize_int(safe_get(venue, 'capacity')),
                    'surface': normalize_string(safe_get(venue, 'surface')),
                    'roof_type': normalize_string(safe_get(venue, 'roof_type')),
                    'latitude': lat,
                    'longitude': lng
                })
            return venue_api_id
        return None
    
    def transform_venues(self, teams_data: Dict[str, Any]) -> None:
        """
        Extract and transform venue data from teams.
        
        Args:
            teams_data: Raw teams JSON data
        """
        if not teams_data:
            return
            
        teams_list = safe_get(teams_data, 'teams', default=[])
        
        for team in teams_list:
            venue = safe_get(team, 'venue')
            if venue:
                self._extract_venue(venue)
    
    def transform_teams(self, teams_data: Dict[str, Any], hierarchy_data: Dict[str, Any] = None) -> None:
        """
        Transform teams data using UUIDs from API.
        
        Args:
            teams_data: Raw teams JSON data
            hierarchy_data: Optional hierarchy data for conference/division mapping
        """
        if not teams_data:
            return
            
        teams_list = safe_get(teams_data, 'teams', default=[])
        
        for team in teams_list:
            api_team_id = normalize_uuid(safe_get(team, 'id'))
            if not api_team_id:
                continue
                
            # Use API UUID directly for team_id
            self.team_id_map[api_team_id] = api_team_id
            
            # Get conference and division
            conference_name = normalize_string(safe_get(team, 'conference', 'name'))
            division_name = normalize_string(safe_get(team, 'division', 'name'))
            
            conference_id = self.conference_id_map.get(conference_name) if conference_name else None
            division_id = None
            if conference_name and division_name:
                # Find division by conference and name
                for (conf_id, div_name), div_uuid in self.division_id_map.items():
                    if conf_id == conference_id and div_name == division_name:
                        division_id = div_uuid
                        break
            
            # Get venue ID from venue_id_map (keyed by venue API ID)
            venue = safe_get(team, 'venue')
            venue_id = None
            if venue:
                venue_api_id = normalize_uuid(safe_get(venue, 'id'))
                venue_id = self.venue_id_map.get(venue_api_id) if venue_api_id else None
            
            self.teams.append({
                'team_id': api_team_id,  # Use API UUID directly
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
    
    def transform_seasons(self, seasons_data: Dict[str, Any]) -> None:
        """
        Transform seasons data using UUIDs.
        
        Args:
            seasons_data: Raw seasons JSON data
        """
        if not seasons_data:
            return
            
        seasons_list = safe_get(seasons_data, 'seasons', default=[])
        
        for season in seasons_list:
            year = normalize_int(safe_get(season, 'year'))
            type_code = normalize_string(safe_get(season, 'type', 'code'))
            season_api_id = normalize_uuid(safe_get(season, 'id'))
            
            if year and type_code:
                key = (year, type_code)
                if key not in self.season_id_map:
                    # Use API UUID if available, otherwise generate one
                    if season_api_id:
                        season_uuid = season_api_id
                    else:
                        season_uuid = str(uuid.uuid4())
                    
                    self.seasons.append({
                        'season_id': season_uuid,
                        'year': year,
                        'start_date': normalize_date(safe_get(season, 'start_date')),
                        'end_date': normalize_date(safe_get(season, 'end_date')),
                        'status': normalize_string(safe_get(season, 'status')),
                        'type_code': type_code
                    })
                    
                    self.season_id_map[key] = season_uuid
    
    def transform_players(self, rosters_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Transform player data from rosters using UUIDs from API.
        Also extracts venues and conference/division info from roster data.
        
        Args:
            rosters_data: Dictionary of team_id -> roster data
        """
        if not rosters_data:
            return
        
        for team_api_id, roster_data in rosters_data.items():
            # Extract venue from roster if present
            venue = safe_get(roster_data, 'venue')
            if venue:
                self._extract_venue(venue)
            
            # Extract conference and division from roster if not already captured
            conf_data = safe_get(roster_data, 'conference')
            if conf_data:
                conf_name = normalize_string(safe_get(conf_data, 'name'))
                conf_api_id = normalize_uuid(safe_get(conf_data, 'id'))
                conf_alias = normalize_string(safe_get(conf_data, 'alias'))
                
                if conf_name and conf_api_id and conf_api_id not in [c['conference_id'] for c in self.conferences]:
                    self.conference_id_map[conf_name] = conf_api_id
                    self.conferences.append({
                        'conference_id': conf_api_id,
                        'name': conf_name,
                        'alias': conf_alias
                    })
            
            div_data = safe_get(roster_data, 'division')
            if div_data and conf_data:
                div_name = normalize_string(safe_get(div_data, 'name'))
                div_api_id = normalize_uuid(safe_get(div_data, 'id'))
                div_alias = normalize_string(safe_get(div_data, 'alias'))
                conf_api_id = normalize_uuid(safe_get(conf_data, 'id'))
                
                if div_name and div_api_id and div_api_id not in [d['division_id'] for d in self.divisions]:
                    division_key = (conf_api_id, div_name)
                    self.division_id_map[division_key] = div_api_id
                    self.divisions.append({
                        'division_id': div_api_id,
                        'name': div_name,
                        'alias': div_alias,
                        'conference_id': conf_api_id
                    })
            
            team_db_id = self.team_id_map.get(team_api_id)
            if not team_db_id:
                continue
            
            players_list = safe_get(roster_data, 'players', default=[])
            
            for player in players_list:
                api_player_id = normalize_uuid(safe_get(player, 'id'))
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
                
                # Skip if still no last_name
                if not last_name:
                    last_name = "Unknown"  # Use placeholder
                
                if api_player_id not in self.player_id_map:
                    self.player_id_map[api_player_id] = api_player_id  # Use API UUID directly
                    
                    # Get position - could be string or object
                    position = safe_get(player, 'position')
                    if isinstance(position, dict):
                        position = safe_get(position, 'name') or safe_get(position, 'abbr')
                    position = normalize_string(position)
                    
                    # Convert height to inches (INTEGER)
                    height = convert_height_to_inches(safe_get(player, 'height'))
                    
                    self.players.append({
                        'player_id': api_player_id,  # Use API UUID directly
                        'first_name': first_name,
                        'last_name': last_name,
                        'abbr_name': normalize_string(safe_get(player, 'abbr_name')) or normalize_string(safe_get(player, 'name', 'abbr')),
                        'birth_place': normalize_string(safe_get(player, 'birth_place')),
                        'position': position,
                        'height': height,  # INTEGER in inches
                        'weight': normalize_int(safe_get(player, 'weight')),
                        'status': normalize_string(safe_get(player, 'status')),
                        'eligibility': normalize_string(safe_get(player, 'eligibility')),
                        'team_id': team_db_id
                    })
    
    def transform_coaches(self, rosters_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Transform coach data from rosters using UUIDs.
        
        Args:
            rosters_data: Dictionary of team_id -> roster data
        """
        if not rosters_data:
            return
        
        for team_api_id, roster_data in rosters_data.items():
            team_db_id = self.team_id_map.get(team_api_id)
            if not team_db_id:
                continue
            
            coaches_list = safe_get(roster_data, 'coaches', default=[])
            
            for coach in coaches_list:
                coach_api_id = normalize_uuid(safe_get(coach, 'id'))
                
                # Get name - could be in different formats
                full_name = normalize_string(safe_get(coach, 'full_name'))
                if not full_name:
                    # Try building from first/last
                    first = normalize_string(safe_get(coach, 'first_name'))
                    last = normalize_string(safe_get(coach, 'last_name'))
                    if first and last:
                        full_name = f"{first} {last}"
                    elif last:
                        full_name = last
                
                if full_name:
                    # Use API UUID if available, otherwise generate one
                    if coach_api_id:
                        coach_uuid = coach_api_id
                    else:
                        coach_uuid = str(uuid.uuid4())
                    
                    self.coaches.append({
                        'coach_id': coach_uuid,
                        'full_name': full_name,
                        'position': normalize_string(safe_get(coach, 'position')),
                        'team_id': team_db_id
                    })
    
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
                api_player_id = normalize_uuid(safe_get(player_stat, 'id'))
                if not api_player_id:
                    continue
                
                player_db_id = self.player_id_map.get(api_player_id)
                if not player_db_id:
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
        
        poll_id = normalize_uuid(safe_get(rankings_data, 'poll', 'id')) or str(uuid.uuid4())
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
            team_api_id = normalize_uuid(safe_get(rank_item, 'id'))
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
            home = item.get('home') or item.get('home_team') or {}
            away = item.get('away') or item.get('away_team') or {}
            venue = item.get('venue') or {}
            event_time = item.get('scheduled') or item.get('date') or item.get('start_time')

            home_api_id = normalize_uuid(home.get('id')) if isinstance(home, dict) else None
            away_api_id = normalize_uuid(away.get('id')) if isinstance(away, dict) else None
            venue_name = normalize_string(venue.get('name')) if isinstance(venue, dict) else None

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
            'divisions': self.divisions,
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


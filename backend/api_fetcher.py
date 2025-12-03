"""
API Fetcher Module for Sportradar NCAAFB APIs.

This module handles fetching data from all required Sportradar API endpoints.
"""

import os
import sys
import requests
import json
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.utils.helpers import save_json_file, get_project_root, ensure_dir
except ImportError:
    from utils.helpers import save_json_file, get_project_root, ensure_dir

# Load environment variables
load_dotenv()


class APIFetcher:
    """Handles API requests to Sportradar NCAAFB endpoints."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the API fetcher.
        
        Args:
            api_key: Sportradar API key. If None, reads from environment.
        """
        # Load from .env file in backend directory
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
        
        self.api_key = api_key or os.getenv('SPORTRADAR_API_KEY')
        if not self.api_key:
            print("⚠️  WARNING: SPORTRADAR_API_KEY not found in .env file!")
            print("   Using default trial key. For production, set your API key in .env")
            self.api_key = '6dP4ysShCJmktrukYUWKueZNV9A6aL8tCU89ck2L'
        self.base_url = "https://api.sportradar.com/ncaafb/trial/v7/en"
        self.headers = {
            "accept": "application/json",
            "x-api-key": self.api_key
        }
        self.raw_json_dir = os.path.join(get_project_root(), 'backend', 'raw_json')
        ensure_dir(self.raw_json_dir)
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Make an API request to the specified endpoint.
        
        Args:
            endpoint: API endpoint path (relative to base_url)
            params: Optional query parameters
            
        Returns:
            JSON response as dictionary or None if request fails
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {endpoint}: {e}")
            return None
    
    def _save_raw_response(self, data: Dict[str, Any], filename: str) -> None:
        """
        Save raw API response to JSON file.
        
        Args:
            data: Response data to save
            filename: Filename (without path)
        """
        filepath = os.path.join(self.raw_json_dir, filename)
        save_json_file(data, filepath)
        print(f"Saved raw response to {filename}")
    
    def fetch_league_hierarchy(self) -> Optional[Dict[str, Any]]:
        """Fetch league hierarchy (conferences, divisions)."""
        print("Fetching league hierarchy...")
        data = self._make_request("league/hierarchy.json")
        if data:
            self._save_raw_response(data, "league_hierarchy.json")
        return data
    
    def fetch_teams(self) -> Optional[Dict[str, Any]]:
        """Fetch all teams."""
        print("Fetching teams...")
        data = self._make_request("league/teams.json")
        if data:
            self._save_raw_response(data, "teams.json")
        return data
    
    def fetch_seasons(self) -> Optional[Dict[str, Any]]:
        """Fetch all seasons."""
        print("Fetching seasons...")
        data = self._make_request("league/seasons.json")
        if data:
            self._save_raw_response(data, "seasons.json")
        return data
    
    def fetch_team_roster(self, team_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch roster for a specific team.
        
        Args:
            team_id: Team ID
            
        Returns:
            Team roster data
        """
        print(f"Fetching roster for team {team_id}...")
        data = self._make_request(f"teams/{team_id}/full_roster.json")
        if data:
            filename = f"roster_{team_id}.json"
            self._save_raw_response(data, filename)
        return data
    
    def fetch_rankings_current(self, year: int = 2025) -> Optional[Dict[str, Any]]:
        """
        Fetch current week rankings.
        
        Args:
            year: Season year
        """
        print(f"Fetching current rankings for {year}...")
        data = self._make_request(f"polls/AP25/{year}/rankings.json")
        if data:
            self._save_raw_response(data, f"rankings_current_{year}.json")
        return data
    
    def fetch_rankings_by_week(self, year: int = 2025, week: int = 1) -> Optional[Dict[str, Any]]:
        """
        Fetch rankings for a specific week.
        
        Args:
            year: Season year
            week: Week number
        """
        print(f"Fetching rankings for {year} week {week}...")
        data = self._make_request(f"polls/AP25/{year}/{week:02d}/rankings.json")
        if data:
            self._save_raw_response(data, f"rankings_{year}_week_{week:02d}.json")
        return data
    
    def fetch_seasonal_statistics(self, year: int = 2025, season_type: str = "REG", 
                                  team_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Fetch seasonal statistics for a team.
        
        Args:
            year: Season year
            season_type: Season type (REG, PST, etc.)
            team_id: Team ID (if None, will need to fetch for all teams)
        """
        if not team_id:
            return None
        print(f"Fetching seasonal statistics for team {team_id}...")
        data = self._make_request(f"seasons/{year}/{season_type}/teams/{team_id}/statistics.json")
        if data:
            filename = f"season_stats_{year}_{season_type}_{team_id}.json"
            self._save_raw_response(data, filename)
        return data
    
    def fetch_player_profile(self, player_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch player profile.
        
        Args:
            player_id: Player ID
        """
        print(f"Fetching player profile for {player_id}...")
        data = self._make_request(f"players/{player_id}/profile.json")
        if data:
            filename = f"player_{player_id}.json"
            self._save_raw_response(data, filename)
        return data

    def fetch_season_schedule(self, year: int = 2025, season_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Fetch season schedule for a given year (and optional season type).

        Args:
            year: Season year
            season_type: Optional season type (e.g., REG, PST)
        """
        print(f"Fetching season schedule for {year} {season_type or ''}...")
        # Sportradar endpoints vary; try with type if provided, otherwise use generic
        if season_type:
            endpoint = f"seasons/{year}/{season_type}/schedule.json"
        else:
            endpoint = f"seasons/{year}/schedule.json"

        data = self._make_request(endpoint)
        if data:
            filename = f"season_schedule_{year}.json" if not season_type else f"season_schedule_{year}_{season_type}.json"
            self._save_raw_response(data, filename)
        return data
    
    def fetch_all_data(self, year: int = 2025, season_type: str = "REG", 
                      max_teams: int = None, fetch_player_profiles: bool = True) -> Dict[str, Any]:
        """
        Fetch all required data from APIs.
        
        Args:
            year: Season year
            season_type: Season type
            max_teams: Maximum number of teams to fetch rosters for (None = all teams)
            fetch_player_profiles: Whether to fetch individual player profiles
            
        Returns:
            Dictionary containing all fetched data
        """
        print("=" * 60)
        print(f"Starting API data fetch for year {year}...")
        print("=" * 60)
        
        all_data = {}
        
        # Core data
        all_data['hierarchy'] = self.fetch_league_hierarchy()
        time.sleep(1)  # Rate limiting
        
        all_data['teams'] = self.fetch_teams()
        time.sleep(1)
        
        all_data['seasons'] = self.fetch_seasons()
        time.sleep(1)
        
        # Rankings
        all_data['rankings_current'] = self.fetch_rankings_current(year)
        time.sleep(1)
        
        all_data['rankings_week1'] = self.fetch_rankings_by_week(year, week=1)
        time.sleep(1)

        # Season schedule
        all_data['season_schedule'] = self.fetch_season_schedule(year, season_type)
        time.sleep(1)
        
        # Fetch rosters for all teams
        if all_data.get('teams') and 'teams' in all_data['teams']:
            all_data['rosters'] = {}
            all_data['player_profiles'] = {}
            teams = all_data['teams']['teams']
            num_teams = min(max_teams, len(teams)) if max_teams else len(teams)
            print(f"\nFetching rosters for {num_teams} teams...")
            
            for i, team in enumerate(teams[:num_teams], 1):
                team_id = team.get('id')
                if team_id:
                    roster = self.fetch_team_roster(team_id)
                    if roster:
                        all_data['rosters'][team_id] = roster
                        
                        # Fetch player profiles if enabled
                        if fetch_player_profiles and 'players' in roster:
                            for player in roster['players'][:3]:  # Limit to 3 players per team for demo
                                player_id = player.get('id')
                                if player_id and player_id not in all_data['player_profiles']:
                                    profile = self.fetch_player_profile(player_id)
                                    if profile:
                                        all_data['player_profiles'][player_id] = profile
                                    time.sleep(1)
                    
                    time.sleep(1)  # Rate limiting
                    if i % 10 == 0:
                        print(f"  Progress: {i}/{num_teams} teams")
        
        # Fetch seasonal statistics for a sample of teams
        if all_data.get('teams') and 'teams' in all_data['teams']:
            all_data['season_stats'] = {}
            teams = all_data['teams']['teams']
            num_stats = min(5, len(teams))
            
            print(f"\nFetching seasonal statistics for {num_stats} teams...")
            for i, team in enumerate(teams[:num_stats], 1):
                team_id = team.get('id')
                if team_id:
                    stats = self.fetch_seasonal_statistics(year, season_type, team_id)
                    if stats:
                        all_data['season_stats'][team_id] = stats
                    time.sleep(1)
        
        print("\n" + "=" * 60)
        print("API data fetch completed!")
        print("=" * 60)
        
        return all_data


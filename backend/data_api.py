"""
Data API Service for Frontend.

This module provides REST API endpoints to serve database data
to the frontend application.
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.db_connection import DatabaseConnection
except ImportError:
    from db_connection import DatabaseConnection

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Global database connection
db = None


def get_db():
    """Get or create database connection."""
    global db
    if db is None:
        db = DatabaseConnection()
        db.connect()
    return db


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'NCAAFB Data API'
    })


@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get all teams."""
    try:
        db = get_db()
        query = """
            SELECT 
                t.team_id,
                t.market,
                t.name,
                t.alias,
                t.founded,
                t.mascot,
                t.fight_song,
                t.championships_won,
                t.conference_id,
                t.division_id,
                t.venue_id,
                c.name as conference_name,
                d.name as division_name,
                v.name as venue_name
            FROM teams t
            LEFT JOIN conferences c ON t.conference_id = c.conference_id
            LEFT JOIN divisions d ON t.division_id = d.division_id
            LEFT JOIN venues v ON t.venue_id = v.venue_id
            ORDER BY t.name
        """
        success, results, error = db.execute_query(query)
        
        if not success:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'teams': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/teams/<team_id>', methods=['GET'])
def get_team(team_id):
    """Get a specific team by ID."""
    try:
        db = get_db()
        query = """
            SELECT 
                t.*,
                c.name as conference_name,
                d.name as division_name,
                v.name as venue_name,
                v.city as venue_city,
                v.state as venue_state
            FROM teams t
            LEFT JOIN conferences c ON t.conference_id = c.conference_id
            LEFT JOIN divisions d ON t.division_id = d.division_id
            LEFT JOIN venues v ON t.venue_id = v.venue_id
            WHERE t.team_id = %s
        """
        success, results, error = db.execute_query(query, (team_id,))
        
        if not success:
            return jsonify({'error': error}), 500
        
        if not results:
            return jsonify({'error': 'Team not found'}), 404
        
        return jsonify(results[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/players', methods=['GET'])
def get_players():
    """Get all players."""
    try:
        db = get_db()
        team_id = request.args.get('team_id')
        
        if team_id:
            query = """
                SELECT 
                    p.*,
                    t.name as team_name,
                    t.market as team_market
                FROM players p
                LEFT JOIN teams t ON p.team_id = t.team_id
                WHERE p.team_id = %s
                ORDER BY p.last_name, p.first_name
            """
            success, results, error = db.execute_query(query, (team_id,))
        else:
            query = """
                SELECT 
                    p.*,
                    t.name as team_name,
                    t.market as team_market
                FROM players p
                LEFT JOIN teams t ON p.team_id = t.team_id
                ORDER BY p.last_name, p.first_name
            """
            success, results, error = db.execute_query(query)
        
        if not success:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'players': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/players/<player_id>', methods=['GET'])
def get_player(player_id):
    """Get a specific player by ID."""
    try:
        db = get_db()
        query = """
            SELECT 
                p.*,
                t.name as team_name,
                t.market as team_market
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE p.player_id = %s
        """
        success, results, error = db.execute_query(query, (player_id,))
        
        if not success:
            return jsonify({'error': error}), 500
        
        if not results:
            return jsonify({'error': 'Player not found'}), 404
        
        return jsonify(results[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/player-statistics', methods=['GET'])
def get_player_statistics():
    """Get player statistics."""
    try:
        db = get_db()
        player_id = request.args.get('player_id')
        team_id = request.args.get('team_id')
        season_id = request.args.get('season_id')
        
        query = """
            SELECT 
                ps.*,
                p.first_name,
                p.last_name,
                p.position,
                t.name as team_name,
                s.year as season_year,
                s.type_code as season_type
            FROM player_statistics ps
            JOIN players p ON ps.player_id = p.player_id
            JOIN teams t ON ps.team_id = t.team_id
            JOIN seasons s ON ps.season_id = s.season_id
        """
        
        conditions = []
        params = []
        
        if player_id:
            conditions.append("ps.player_id = %s")
            params.append(player_id)
        if team_id:
            conditions.append("ps.team_id = %s")
            params.append(team_id)
        if season_id:
            conditions.append("ps.season_id = %s")
            params.append(season_id)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY ps.rushing_yards DESC NULLS LAST, ps.receiving_yards DESC NULLS LAST"
        
        success, results, error = db.execute_query(query, tuple(params) if params else None)
        
        if not success:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'statistics': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    """Get rankings."""
    try:
        db = get_db()
        week = request.args.get('week', type=int)
        season_id = request.args.get('season_id')
        
        query = """
            SELECT 
                r.*,
                t.name as team_name,
                t.market as team_market,
                s.year as season_year,
                s.type_code as season_type
            FROM rankings r
            JOIN teams t ON r.team_id = t.team_id
            JOIN seasons s ON r.season_id = s.season_id
        """
        
        conditions = []
        params = []
        
        if week:
            conditions.append("r.week = %s")
            params.append(week)
        if season_id:
            conditions.append("r.season_id = %s")
            params.append(season_id)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY r.week DESC, r.rank ASC"
        
        success, results, error = db.execute_query(query, tuple(params) if params else None)
        
        if not success:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'rankings': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/seasons', methods=['GET'])
def get_seasons():
    """Get all seasons."""
    try:
        db = get_db()
        query = """
            SELECT *
            FROM seasons
            ORDER BY year DESC, type_code
        """
        success, results, error = db.execute_query(query)
        
        if not success:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'seasons': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/conferences', methods=['GET'])
def get_conferences():
    """Get all conferences."""
    try:
        db = get_db()
        query = """
            SELECT 
                c.*,
                COUNT(DISTINCT t.team_id) as team_count
            FROM conferences c
            LEFT JOIN teams t ON c.conference_id = t.conference_id
            GROUP BY c.conference_id, c.name, c.alias
            ORDER BY c.name
        """
        success, results, error = db.execute_query(query)
        
        if not success:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'conferences': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/season-schedule', methods=['GET'])
def get_season_schedule():
    """Get season schedule (returns cleaned schedule if available, otherwise raw JSON)."""
    try:
        year = request.args.get('year', type=int)
        # Look for cleaned file first
        from backend.utils.helpers import get_project_root, load_json_file

        root = get_project_root()
        candidates = []
        if year:
            candidates.append(os.path.join(root, 'backend', 'clean_data', f'season_schedule_{year}.json'))
            candidates.append(os.path.join(root, 'backend', 'raw_json', f'season_schedule_{year}.json'))
        else:
            # No year provided - try generic
            candidates.append(os.path.join(root, 'backend', 'clean_data', f'season_schedule_2025.json'))
            candidates.append(os.path.join(root, 'backend', 'raw_json', f'season_schedule_2025.json'))

        for path in candidates:
            if os.path.exists(path):
                data = load_json_file(path)
                return jsonify({'schedule': data})

        return jsonify({'schedule': [], 'message': 'No schedule file found for requested year'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/divisions', methods=['GET'])
def get_divisions():
    """Get all divisions."""
    try:
        db = get_db()
        conference_id = request.args.get('conference_id')
        
        if conference_id:
            query = """
                SELECT 
                    d.*,
                    c.name as conference_name
                FROM divisions d
                LEFT JOIN conferences c ON d.conference_id = c.conference_id
                WHERE d.conference_id = %s
                ORDER BY d.name
            """
            success, results, error = db.execute_query(query, (conference_id,))
        else:
            query = """
                SELECT 
                    d.*,
                    c.name as conference_name
                FROM divisions d
                LEFT JOIN conferences c ON d.conference_id = c.conference_id
                ORDER BY c.name, d.name
            """
            success, results, error = db.execute_query(query)
        
        if not success:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'divisions': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/venues', methods=['GET'])
def get_venues():
    """Get all venues."""
    try:
        db = get_db()
        query = """
            SELECT 
                venue_id,
                name,
                city,
                state,
                country,
                zip,
                address,
                capacity,
                surface,
                roof_type,
                latitude,
                longitude
            FROM venues
            ORDER BY name
        """
        success, results, error = db.execute_query(query)
        
        if not success:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'venues': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/coaches', methods=['GET'])
def get_coaches():
    """Get all coaches."""
    try:
        db = get_db()
        team_id = request.args.get('team_id')
        
        if team_id:
            query = """
                SELECT 
                    co.coach_id,
                    co.full_name,
                    co.position,
                    co.team_id,
                    t.name as team_name,
                    t.market as team_market
                FROM coaches co
                JOIN teams t ON co.team_id = t.team_id
                WHERE co.team_id = %s
                ORDER BY co.position, co.full_name
            """
            success, results, error = db.execute_query(query, (team_id,))
        else:
            query = """
                SELECT 
                    co.coach_id,
                    co.full_name,
                    co.position,
                    co.team_id,
                    t.name as team_name,
                    t.market as team_market
                FROM coaches co
                JOIN teams t ON co.team_id = t.team_id
                ORDER BY t.name, co.position, co.full_name
            """
            success, results, error = db.execute_query(query)
        
        if not success:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'coaches': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats/summary', methods=['GET'])
def get_stats_summary():
    """Get summary statistics."""
    try:
        db = get_db()
        
        # Get counts
        queries = {
            'teams': "SELECT COUNT(*) as count FROM teams",
            'players': "SELECT COUNT(*) as count FROM players",
            'coaches': "SELECT COUNT(*) as count FROM coaches",
            'venues': "SELECT COUNT(*) as count FROM venues",
            'conferences': "SELECT COUNT(*) as count FROM conferences",
            'rankings': "SELECT COUNT(*) as count FROM rankings"
        }
        
        summary = {}
        for key, query in queries.items():
            success, results, error = db.execute_query(query)
            if success and results:
                summary[key] = results[0]['count']
            else:
                summary[key] = 0
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='NCAAFB Data API')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5001,
                       help='Port to bind to (default: 5001)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("NCAAFB Data API")
    print("=" * 60)
    print(f"\nStarting server on http://{args.host}:{args.port}")
    print("\nEndpoints:")
    print("  GET  /health              - Health check")
    print("  GET  /api/teams           - Get all teams")
    print("  GET  /api/teams/<id>      - Get team by ID")
    print("  GET  /api/players         - Get all players")
    print("  GET  /api/players/<id>    - Get player by ID")
    print("  GET  /api/player-statistics - Get player stats")
    print("  GET  /api/rankings        - Get rankings")
    print("  GET  /api/seasons          - Get seasons")
    print("  GET  /api/conferences      - Get conferences")
    print("  GET  /api/divisions        - Get divisions")
    print("  GET  /api/venues           - Get venues")
    print("  GET  /api/coaches          - Get coaches")
    print("  GET  /api/stats/summary    - Get summary stats")
    print("\n" + "=" * 60 + "\n")
    
    app.run(host=args.host, port=args.port, debug=args.debug)


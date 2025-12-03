-- Database initialization script for NCAAFB Database Professor
-- This script creates the necessary tables and initial data

-- Create tables (simplified version - actual schema should be imported from your existing database)
CREATE TABLE IF NOT EXISTS conferences (
    conference_id UUID PRIMARY KEY,
    name VARCHAR(100),
    alias VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS divisions (
    division_id UUID PRIMARY KEY,
    name VARCHAR(100),
    conference_id UUID REFERENCES conferences(conference_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS teams (
    team_id UUID PRIMARY KEY,
    market VARCHAR(100),
    name VARCHAR(100),
    alias VARCHAR(10),
    founded INTEGER,
    mascot VARCHAR(100),
    fight_song VARCHAR(255),
    championships_won INTEGER,
    conference_id UUID REFERENCES conferences(conference_id),
    division_id UUID REFERENCES divisions(division_id),
    venue_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS players (
    player_id UUID PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    position VARCHAR(10),
    height INTEGER,
    weight INTEGER,
    status VARCHAR(50),
    team_id UUID REFERENCES teams(team_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS venues (
    venue_id UUID PRIMARY KEY,
    name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    capacity INTEGER,
    surface VARCHAR(50),
    roof_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS seasons (
    season_id UUID PRIMARY KEY,
    year INTEGER,
    type_code VARCHAR(10),
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rankings (
    ranking_id UUID PRIMARY KEY,
    team_id UUID REFERENCES teams(team_id),
    season_id UUID REFERENCES seasons(season_id),
    week INTEGER,
    rank INTEGER,
    prev_rank INTEGER,
    points DECIMAL(10,2),
    wins INTEGER,
    losses INTEGER,
    poll_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS player_statistics (
    stat_id UUID PRIMARY KEY,
    player_id UUID REFERENCES players(player_id),
    team_id UUID REFERENCES teams(team_id),
    season_id UUID REFERENCES seasons(season_id),
    games_played INTEGER,
    rushing_yards INTEGER,
    rushing_touchdowns INTEGER,
    receiving_yards INTEGER,
    receiving_touchdowns INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS coaches (
    coach_id UUID PRIMARY KEY,
    full_name VARCHAR(255),
    position VARCHAR(100),
    team_id UUID REFERENCES teams(team_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_teams_conference ON teams(conference_id);
CREATE INDEX IF NOT EXISTS idx_teams_division ON teams(division_id);
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_rankings_team ON rankings(team_id);
CREATE INDEX IF NOT EXISTS idx_rankings_season ON rankings(season_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_statistics(player_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_team ON player_statistics(team_id);
CREATE INDEX IF NOT EXISTS idx_coaches_team ON coaches(team_id);
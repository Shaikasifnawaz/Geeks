-- NCAAFB Database Schema - Complete Relational Design
-- Creates 9 normalized tables with UUID primary keys and proper relationships

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS player_statistics CASCADE;
DROP TABLE IF EXISTS rankings CASCADE;
DROP TABLE IF EXISTS coaches CASCADE;
DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS divisions CASCADE;
DROP TABLE IF EXISTS venues CASCADE;
DROP TABLE IF EXISTS seasons CASCADE;
DROP TABLE IF EXISTS conferences CASCADE;

-- 1. CONFERENCES Table
CREATE TABLE conferences (
    conference_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    alias VARCHAR(100)
);

-- 2. DIVISIONS Table
CREATE TABLE divisions (
    division_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    alias VARCHAR(100),
    conference_id UUID REFERENCES conferences(conference_id) ON DELETE SET NULL
);

-- 3. VENUES Table
CREATE TABLE venues (
    venue_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(50) DEFAULT 'USA',
    zip VARCHAR(20),
    address VARCHAR(255),
    capacity INTEGER,
    surface VARCHAR(50),
    roof_type VARCHAR(50),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8)
);

-- 4. SEASONS Table
CREATE TABLE seasons (
    season_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    year INTEGER NOT NULL,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50),
    type_code VARCHAR(20) NOT NULL,
    UNIQUE(year, type_code)
);

-- 5. TEAMS Table
CREATE TABLE teams (
    team_id UUID PRIMARY KEY,
    market VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    alias VARCHAR(100),
    founded INTEGER,
    mascot VARCHAR(100),
    fight_song VARCHAR(255),
    championships_won INTEGER DEFAULT 0,
    conference_id UUID REFERENCES conferences(conference_id) ON DELETE SET NULL,
    division_id UUID REFERENCES divisions(division_id) ON DELETE SET NULL,
    venue_id UUID REFERENCES venues(venue_id) ON DELETE SET NULL
);

-- 6. PLAYERS Table
CREATE TABLE players (
    player_id UUID PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    abbr_name VARCHAR(50),
    birth_place VARCHAR(255),
    position VARCHAR(50),
    height INTEGER,
    weight INTEGER,
    status VARCHAR(50),
    eligibility VARCHAR(50),
    team_id UUID REFERENCES teams(team_id) ON DELETE CASCADE
);

-- 7. PLAYER_STATISTICS Table
CREATE TABLE player_statistics (
    stat_id SERIAL PRIMARY KEY,
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    season_id UUID NOT NULL REFERENCES seasons(season_id) ON DELETE CASCADE,
    games_played INTEGER,
    games_started INTEGER,
    rushing_yards INTEGER,
    rushing_touchdowns INTEGER,
    receiving_yards INTEGER,
    receiving_touchdowns INTEGER,
    kick_return_yards INTEGER,
    fumbles INTEGER,
    UNIQUE(player_id, team_id, season_id)
);

-- 8. RANKINGS Table
CREATE TABLE rankings (
    ranking_id SERIAL PRIMARY KEY,
    poll_id UUID,
    poll_name VARCHAR(100),
    season_id UUID REFERENCES seasons(season_id) ON DELETE CASCADE,
    week INTEGER,
    effective_time TIMESTAMP,
    team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    prev_rank INTEGER,
    points INTEGER,
    fp_votes INTEGER,
    wins INTEGER,
    losses INTEGER,
    ties INTEGER
);

-- 9. COACHES Table
CREATE TABLE coaches (
    coach_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    position VARCHAR(100),
    team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_teams_conference ON teams(conference_id);
CREATE INDEX idx_teams_division ON teams(division_id);
CREATE INDEX idx_teams_venue ON teams(venue_id);
CREATE INDEX idx_divisions_conference ON divisions(conference_id);
CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_player_stats_player ON player_statistics(player_id);
CREATE INDEX idx_player_stats_team ON player_statistics(team_id);
CREATE INDEX idx_player_stats_season ON player_statistics(season_id);
CREATE INDEX idx_rankings_team ON rankings(team_id);
CREATE INDEX idx_rankings_season ON rankings(season_id);
CREATE INDEX idx_coaches_team ON coaches(team_id);

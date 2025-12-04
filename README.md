NCAAFB Data Platform — Architecture Overview

This platform provides a complete NCAA Football data experience through interactive dashboards, structured APIs, and an AI-powered query engine (“Database Professor”).
It is built with three coordinated services deployed on Render, all connected to a shared PostgreSQL database.

🔵 Frontend (Streamlit Interface)

URL: https://ncaafb-frontend.onrender.com

This is the primary user-facing application where visitors can:

Explore NCAA football data through interactive dashboards

View teams, players, rankings, and stats

Ask natural language questions to the AI-powered database professor

The frontend communicates with both the Data API and the LLM API to fetch structured data and generate insights.

🧠 LLM API (AI Query Engine)

URL: https://ncaafb-llm-apii.onrender.com

This service processes natural language questions and converts them into intelligent, SQL-driven answers.

How It Works

The frontend sends questions to the /query endpoint.

The LLM API:

Interprets the question

Generates SQL queries

Executes them on the PostgreSQL database

Returns structured results and insights

Request Format
POST /query
{
  "question": "natural language question",
  "model": "gemini-2.5-flash",
  "max_results": 100
}

📊 Data API (Structured Data Service)

URL: https://ncaafb-data-api.onrender.com

This backend service exposes organized data endpoints that power the dashboards.

Available Endpoints

Teams: /api/teams

Players: /api/players

Player Statistics: /api/player-statistics

Rankings: /api/rankings

Seasons: /api/seasons

Conferences & Divisions: /api/conferences, /api/divisions

Venues: /api/venues

Coaches: /api/coaches

Summary Stats: /api/stats/summary

These endpoints allow the frontend to render fast, structured, and reliable data views.

🏗️ System Architecture Overview

The platform is composed of three interconnected services:

1️⃣ Frontend (Streamlit)

Serves the user interface

Pulls structured data from the Data API

Sends natural language queries to the LLM API

Renders dashboards and insight responses

2️⃣ Data API

Provides direct access to structured NCAA football datasets

Performs standard DB queries

Supports all frontend dashboards

3️⃣ LLM API

Converts natural language into SQL

Executes SQL on PostgreSQL

Returns intelligent insights

All services use the same PostgreSQL database, ensuring data consistency across dashboards and AI-generated responses.

🩺 Health Check Endpoints

Use these URLs to verify service status:

Frontend: https://ncaafb-frontend.onrender.com

Data API: https://ncaafb-data-api.onrender.com/health

LLM API: https://ncaafb-llm-apii.onrender.com/health

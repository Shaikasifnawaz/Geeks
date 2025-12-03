# NCAAFB Database Professor

A college football data analytics platform with an AI-powered database professor that can answer questions about teams, players, rankings, and statistics.

## Deployment Instructions for Render.com

### 1. Create Render Services

1. Sign up at [render.com](https://render.com)
2. Connect your GitHub account
3. Create a new Web Service and select this repository

### 2. Database Setup

1. Create a PostgreSQL database on Render
2. Note the connection details (host, port, database name, user, password)
3. Update the `.env` file in the `backend` directory with your database connection details:
   ```
   DB_HOST=dpg-d4nvetf5r7bs73cacul0-a.oregon-postgres.render.com
   DB_PORT=5432
   DB_NAME=ncaafb_databaseguvi
   DB_USER=ncaafb_databaseguvi_user
   DB_PASSWORD=DFwIzA9EYnj8W0fwwPY7mKs9XlF02XCi
   ```

### 3. Environment Variables

Set the following environment variables for all services:

- `DB_HOST` - Your PostgreSQL host
- `DB_PORT` - Your PostgreSQL port (usually 5432)
- `DB_NAME` - Your database name
- `DB_USER` - Your database user
- `DB_PASSWORD` - Your database password
- `GEMINI_API_KEY` - Your Google Gemini API key (for LLM service)

### 4. Service Configuration

#### Data API Service
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn --bind 0.0.0.0:$PORT backend.data_api:app`

#### LLM API Service
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn --bind 0.0.0.0:$PORT backend.llm_api:app`

#### Frontend Service
- Build Command: `pip install -r requirements.txt`
- Start Command: `streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0`

### 5. Run Data Pipeline

After setting up your database and environment variables, run the data pipeline to populate your database with data from SportsRadar:

```bash
python run_pipeline.py
```

This will fetch data from SportsRadar API and populate your database.

### 6. Update Frontend Configuration

After deploying your backend services, update the frontend environment variables:
- `API_BASE_URL` - URL of your Data API service
- `LLM_API_BASE_URL` - URL of your LLM API service
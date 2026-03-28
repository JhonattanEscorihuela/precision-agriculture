# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack precision agriculture application that analyzes crop health using Sentinel-2 satellite imagery. The system combines geospatial polygon management with NDVI-based health classification using both classical filtering and U-Net deep learning approaches.

**Stack:**
- Backend: FastAPI (async) + PostgreSQL + SQLModel
- Frontend: Next.js 16 (App Router) + TypeScript + React 19 + Leaflet
- ML Research: Jupyter notebooks with Sentinel-2 data processing, NDVI analysis, and U-Net segmentation

## Development Commands

### Frontend (from `frontend/`)
```bash
npm run dev          # Start development server on localhost:3000
npm run build        # Production build
npm run lint         # Run ESLint
```

### Backend (from `backend/`)
```bash
# Development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/
```

### Docker Compose (from root)
```bash
docker-compose up          # Start all services (frontend:3000, backend:8000, db:5432)
docker-compose down        # Stop services
```

### Jupyter Notebooks (from `backend/core/`)
```bash
# Create/activate virtual environment first
python -m venv venv_39
source venv_39/bin/activate  # or venv_39\Scripts\activate on Windows
pip install -r requirements.txt

# Launch Jupyter
jupyter lab
```

**Environment variables required for notebooks:**
- `SENTINEL_CLIENT_ID` - Copernicus DataSpace API client ID
- `SENTINEL_CLIENT_SECRET` - Copernicus DataSpace API secret
- Store in `backend/core/.env` file

## Architecture

### Backend Structure (`backend/app/`)
```
app/
├── api/endpoints/     # Route handlers (polygons.py, auth.py)
├── crud/              # Database operations (CRUD functions)
├── models/            # SQLModel database models (user.py, polygon.py)
├── schemas/           # Pydantic request/response schemas
├── services/          # Business logic (polygons_logic.py, auth_logic.py)
├── core/              # Configuration (config.py, security.py)
└── database.py        # Async DB session setup
```

**Backend patterns:**
- All database operations use async SQLAlchemy with AsyncSession
- Models use SQLModel (combines SQLAlchemy + Pydantic)
- CRUD layer handles all database queries
- Services layer contains business logic (e.g., area calculations)
- API endpoints are thin orchestration layers

### Frontend Structure (`frontend/app/`)
```
app/
├── components/        # Reusable UI components (LeafletMap, PolygonDrawer, etc.)
├── context/           # React Context for state management
├── cultivos/          # Route: /cultivos
├── nueva-parcela/     # Route: /nueva-parcela
├── layout.tsx         # Root layout
└── page.tsx           # Home page
```

**Frontend patterns:**
- Next.js App Router with TypeScript
- Leaflet + leaflet-draw for interactive map and polygon drawing
- Context API for sharing polygon state across components
- Tailwind CSS for styling

### ML Research Pipeline (`backend/core/`)

**Notebooks:**
1. `01_maqueta_sintetica.ipynb` - Synthetic data pipeline for testing segmentation models
2. `02_pipeline_sentinel_real.ipynb` - Real Sentinel-2 data processing pipeline

**Pipeline flow (notebook 02):**
1. Authenticate with Copernicus DataSpace API (OAuth2)
2. Download Sentinel-2 bands (B04/Red, B08/NIR) for parcel polygon
3. Calculate NDVI: `(B08 - B04) / (B08 + B04)`
4. Create vegetation mask: `NDVI > 0.3`
5. Apply convolutional filter (telecom approach) for texture analysis
6. Train lightweight U-Net for semantic segmentation
7. Classify crop health: combine NDVI + texture → Critical/Alert/Healthy
8. Generate health map visualization (red/yellow/green)

**Key dependencies (core):**
- `rasterio` - GeoTIFF handling
- `geopandas` / `shapely` - Polygon/geometry operations
- `scikit-learn` - IoU/Dice metrics
- `tensorflow` - U-Net model
- `requests-oauthlib` - Sentinel Hub authentication
- `matplotlib` - Visualization

## Database Schema

**Polygons table:**
- `id` (primary key)
- `name` - User-friendly parcel name
- `coordinates` - GeoJSON-style coordinate array
- `area` - Calculated area in square meters
- `created_at` / `updated_at` - ISO timestamp strings

**Users table:**
- `id` (primary key)
- Authentication fields (managed by auth logic)

## Key Workflows

### Adding a new API endpoint
1. Define Pydantic schemas in `app/schemas/`
2. Create database model in `app/models/` (if needed)
3. Implement CRUD functions in `app/crud/`
4. Add business logic to `app/services/`
5. Create route handler in `app/api/endpoints/`
6. Register router in `backend/main.py`
7. Add tests in `backend/tests/`

### Working with Sentinel-2 data
- Always use `.env` for API credentials (never commit secrets)
- GeoJSON coordinates use `[longitude, latitude]` order (CRS84/WGS84)
- Request TIFF format for analysis (not PNG) to preserve float precision
- NDVI values range [-1, 1]; vegetation typically [0.2, 0.8]
- Apply contrast stretching (2-98 percentile) for visualization

### Frontend map integration
- Leaflet maps require dynamic import with `ssr: false` in Next.js
- Use `leaflet-draw` for polygon drawing UI
- Convert Leaflet polygon to GeoJSON before sending to API
- Backend expects coordinates as array of `[lon, lat]` pairs

## Testing

Run tests from `backend/` directory:
```bash
pytest                    # Run all tests
pytest tests/test_polygons.py  # Specific test file
pytest -v                 # Verbose output
```

Tests use pytest with async support. Database fixtures defined in `tests/conftest.py`.

## Important Notes

- **Database URL**: Default `postgresql+asyncpg://postgres:password@db:5432/precision` (docker-compose)
- **CORS**: Backend allows all origins (`allow_origins=["*"]`) - restrict in production
- **Coordinate systems**: GeoJSON/API uses WGS84 (EPSG:4326), lon/lat order
- **Virtual environments**: `backend/core/venv_39/` is gitignored, recreate locally
- **Node modules**: Frontend uses yarn for consistency (see `yarn.lock`)
- **Port conflicts**: Frontend:3000, Backend:8000, PostgreSQL:5432 must be free

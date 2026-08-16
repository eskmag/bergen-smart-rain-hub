# Multi-stage build: Node builds the React app, Python serves both the
# API and the built frontend (api/main.py mounts frontend-react/dist).
# Only explicit COPYs are used below (no `COPY . .`) so nothing outside
# this list — including .env, .git, tests/, docs/ — can ever land in an
# image layer.

FROM node:22-slim AS frontend
WORKDIR /app/frontend-react
COPY frontend-react/package*.json ./
RUN npm ci
COPY frontend-react/index.html frontend-react/vite.config.ts frontend-react/tsconfig*.json ./
COPY frontend-react/public ./public
COPY frontend-react/src ./src
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY backend/ backend/
COPY api/ api/
RUN pip install --no-cache-dir .
COPY data/rain.db data/rain.db
COPY --from=frontend /app/frontend-react/dist frontend-react/dist

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

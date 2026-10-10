# syntax=docker/dockerfile:1

# Abu Dhabi Tourism Digital Twin — two runnable targets:
#
#   docker build --target web -t tourism-twin-web .
#   docker build --target api -t tourism-twin-api .
#
# `web` is the static React app (web/): it only needs the committed
# web/public/data bundle — no Python at runtime.
# `api` is the Python package (`twin` CLI + `twin serve` legacy UI/JSON API):
# it carries the committed lake artifacts, so simulate/serve work out of the
# box; mount "01a - DCT Dataset/" to rebuild the lake or run `twin predict`.

# ---------- web static build ----------
FROM node:22-alpine AS web-build
WORKDIR /build
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build          # vite copies public/ (data bundle) into dist/

FROM nginx:1.27-alpine AS web
COPY web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=web-build /build/dist /usr/share/nginx/html
EXPOSE 80

# ---------- python API / CLI ----------
FROM python:3.13-slim AS api
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Committed lake artifacts (parquet/pkl/json) — enough for simulate and serve.
# analytics.duckdb and raw workbooks are intentionally not built-in.
COPY lake/ ./lake/

EXPOSE 8080
CMD ["twin", "serve", "--host", "0.0.0.0", "--port", "8080"]

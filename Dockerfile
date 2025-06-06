# ── Step 0: pick your base
FROM python:3.11-slim

# ── Step 1: install GDAL & GEOS system libs
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gdal-bin \
      libgdal-dev \
      libgeos-dev \
 && rm -rf /var/lib/apt/lists/*

# ── Step 2: set GDAL/GEOS paths for Python bindings
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# ── Step 3: create app dir & install Python deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Step 4: copy in code + entrypoint
COPY . .
# copy your entrypoint script (see below)
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# ── Step 5: expose port and launch via entrypoint
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]

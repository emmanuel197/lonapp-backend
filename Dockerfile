# Use a Python image based on Debian that includes necessary libraries
FROM python:3.9-slim-buster

# Install GDAL and GEOS libraries and their dependencies
# libgdal-dev includes the GDAL library and headers
# libgeos-dev includes the GEOS library and headers
# postgis is often needed for spatial database interactions
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    libgeos-dev \
    postgis \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL and GEOS library paths within the container
# These paths are standard locations on Debian-based systems after installing the packages
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Collect static files (important for production)
RUN python manage.py collectstatic --noinput

# Run database migrations (optional, can also be a separate Render job)
# RUN python manage.py migrate

# Expose the port the application will run on
# Render automatically sets the PORT environment variable
EXPOSE $PORT

# Command to run the application using Gunicorn
# Replace 'lonapp.wsgi:application' with your actual project.wsgi path
CMD ["gunicorn", "lonapp.wsgi:application", "--bind", "0.0.0.0:$PORT"]

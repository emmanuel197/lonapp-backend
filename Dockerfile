# Use a Python image based on Debian that includes necessary libraries
FROM python:3.9-slim-buster

# Install necessary packages including GDAL and GEOS
# gdal-bin provides GDAL utilities and libraries
# libgeos-dev provides GEOS headers and static libs
# libgeos-c1v5 provides the GEOS runtime shared library (based on previous error hint)
# postgis is often needed for spatial database interactions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgeos-dev \
    libgeos-c1v5 \
    postgis \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Remove explicit environment variables for GDAL/GEOS paths
# Django should find them in standard system locations after installation
# ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
# ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Remove collectstatic from build step
# RUN python manage.py collectstatic --noinput

# Remove migrate from build step (if you had it)
# RUN python manage.py migrate

# Expose the port the application will run on
# Render automatically sets the PORT environment variable
EXPOSE $PORT

# Command to run the application using Gunicorn - collectstatic and migrate will run before this
# Replace 'lonapp.wsgi:application' with your actual project.wsgi path
CMD ["gunicorn", "lonapp.wsgi:application", "--bind", "0.0.0.0:$PORT"]

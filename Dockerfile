# This Dockerfile is designed to be as universal as possible.
# It uses a standard, official Python base image.
# For Docker to "work anywhere," it needs an internet connection to download base images like this one.
# The error you saw earlier was a network problem, not an issue with the Dockerfile itself.

# Use a common and stable version of Python.
# This image is one of the most standard and widely used.
FROM python:3.10

# Set the working directory inside the container.
WORKDIR /app

# Copy the requirements file first. This is a Docker best practice that uses caching
# to speed up future builds if the requirements haven't changed.
COPY requirements.txt .

# Install the Python dependencies listed in your requirements.txt file.
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code into the container.
COPY app/ ./app/

# Set the default command to run your application.
# This command will execute when the container starts.
CMD ["python", "app/finale.py"]
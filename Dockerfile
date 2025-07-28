# 1. Base Image: Use a slim Python base image compatible with linux/amd64
FROM --platform=linux/amd64 python:3.10-slim-buster

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install system dependencies required by OpenCV (a sub-dependency of paddleocr)
# This helps keep the image size down compared to installing full build-essentials
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 4. Copy the application and its dependencies into the container
# This copies everything from your local 'app' folder to the container's '/app' WORKDIR
COPY app/ .

# 5. Install Python packages for offline use
# --no-cache-dir reduces layer size
RUN pip install --no-cache-dir -r requirements.txt

# 6. Set the command to run when the container starts
# This will execute the script automatically
CMD ["python", "finale.py"]
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for opencv, MySQL, Tesseract, etc.
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libsm6 \
    libxext6 \
    libxrender-dev \
    tesseract-ocr \
    libgl1 \
    libmysqlclient-dev \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port (optional if using gunicorn with port binding)
EXPOSE 5000

# Default command to run the app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]

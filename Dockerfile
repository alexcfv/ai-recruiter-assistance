# Use Python 3.11 as base
FROM python:3.11-slim

# Install system dependencies for Node.js and document parsing
RUN apt-get update && apt-get install -y \
    curl \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the entire project
COPY . .

# Install dependencies
RUN pip install -e .

# Make the startup script executable
RUN chmod +x run_all.sh

# Expose ports: 8000 (API) and 5173 (Frontend)
EXPOSE 5173
EXPOSE 8000

# Run everything via the script (it will handle npm install and build)
CMD ["./run_all.sh"]

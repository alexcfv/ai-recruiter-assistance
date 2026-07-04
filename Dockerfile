# Use Python 3.11 as base
FROM python:3.11-slim

# Install system dependencies for Node.js and document parsing
RUN apt-get update && apt-get install -y \
    curl \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files first to install dependencies
COPY pyproject.toml . 
RUN pip install -e .

RUN if [ ! -f config.yaml ]; then cp config.example.yaml config.yaml; fi

# Copy the entire project
COPY . .

RUN chmod +x run_all.sh

# Expose ports: 8000 (API) and 5173 (Frontend)
EXPOSE 8000
EXPOSE 5173

# Run everything via the script (it will handle npm install and build)
CMD ["./run_all.sh"]

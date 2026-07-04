FROM python:3.11-slim

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

COPY . .

RUN pip install -e . && \
    cd frontend && npm install && npm run build && \
    rm -rf node_modules && cd ..

RUN chmod +x run_all.sh

EXPOSE 8000

CMD ["./run_all.sh"]

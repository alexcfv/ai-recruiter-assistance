FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/ .

RUN npm install && npm run build && rm -rf node_modules

FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN pip install -e .

RUN chmod +x run_all.sh

EXPOSE 8000

CMD ["./run_all.sh"]

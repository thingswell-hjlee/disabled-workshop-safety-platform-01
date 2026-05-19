FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

# Note: This container needs privileged mode for GPIO access
EXPOSE 8004

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8004"]

FROM nvcr.io/nvidia/pytorch:24.05-py3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

RUN useradd -m appuser
USER appuser

EXPOSE 8006

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8006"]

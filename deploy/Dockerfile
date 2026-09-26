FROM python:3.13-slim

# LibreOffice нужен прототипу расчётки: чтение .doc и пересчёт формул XLSX.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libreoffice-calc libreoffice-writer fonts-dejavu-core git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV AMERI_DATA_DIR=/data \
    AMERI_DUCT_CALC_DIR=/duct-calc \
    PYTHONUNBUFFERED=1
EXPOSE 8501 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"
CMD ["sh", "deploy/entrypoint.sh"]

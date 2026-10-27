# Версия образа закреплена: пока она не меняется, шаги с LibreOffice и библиотеками Python берутся
# из кэша сервера, и сборка не ходит в Debian и PyPI. Обновлять вручную (например, раз в месяц):
# digest из `docker buildx imagetools inspect python:3.13-slim`.
FROM python:3.13-slim@sha256:b3575dcf816cdacc5292df77a6e3e59b8941631078373a045efa2ac1e9c5c3b2

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

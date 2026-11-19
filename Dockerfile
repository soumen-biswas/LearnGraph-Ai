FROM python:3.15-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt && useradd --create-home appuser
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/staticfiles && chown appuser:appuser /app/staticfiles
USER appuser
EXPOSE 8000
CMD ["sh", "deploy/start.sh"]

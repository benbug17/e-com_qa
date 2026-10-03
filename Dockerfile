# Demo shop (system under test)
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir Flask psycopg2-binary werkzeug itsdangerous
COPY shop_app shop_app
CMD ["python", "-m", "shop_app.app"]

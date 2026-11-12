# alterado -slim
FROM python:3.12-alpine
ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates ./templates
COPY static ./static

VOLUME /data
EXPOSE 8080

# 1 worker + threads: o CSV é protegido por lock dentro do processo
CMD ["gunicorn", "-w", "1", "--threads", "4", "-b", "0.0.0.0:8080", "app:app"]

FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir /app

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x /app/entrypoint.prod.sh

EXPOSE 80

CMD ["/app/entrypoint.prod.sh"]
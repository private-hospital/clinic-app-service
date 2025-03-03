FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir /app

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.10-slim

#RUN useradd -m -r appuser && \
#    mkdir /app && \
#    chown -R appuser /app
#
#COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
#COPY --from=builder /usr/local/bin/ /usr/local/bin/
#
#WORKDIR /app
#
#COPY --chown=appuser:appuser . .

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

#USER appuser

EXPOSE 80

RUN chmod +x /app/entrypoint.prod.sh

CMD ["/app/entrypoint.prod.sh"]
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    nano \
    tzdata

ADD bot/requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --upgrade -r /app/requirements.txt

ADD db/requirements.txt /db/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /db/requirements.txt

CMD ["/app/bot.sh"]
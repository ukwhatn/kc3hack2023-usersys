FROM python:3.11-slim

WORKDIR /app

ADD web/requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --upgrade -r /app/requirements.txt

ADD db/requirements.txt /db/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /db/requirements.txt

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]

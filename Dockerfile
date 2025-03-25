FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libmagic1 \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

COPY ./app /app
COPY requirements.txt .
COPY bootstrap.sh .

RUN chmod +x bootstrap.sh

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["./bootstrap.sh"]

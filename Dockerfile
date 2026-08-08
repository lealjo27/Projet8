FROM python:3.11-slim

WORKDIR /app

# Dépendances mises en cache séparément
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code copié après les dépendances
COPY app/ ./app/

EXPOSE 7860

CMD ["python", "-m", "app.gradio_app"]

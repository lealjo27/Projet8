# Base stable et légère
FROM python:3.11-slim

WORKDIR /home/user/app

# Empêche les logs inutiles et accélère le comportement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Déps système utiles (ajuste si besoin)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git \
      ffmpeg \
      libsm6 \
      libxext6 \
      libgl1 \
      && rm -rf /var/lib/apt/lists/*

# Installer dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier tout le projet
COPY . .

# Port Gradio
EXPOSE 7860

# Démarrage de l’app
CMD ["python", "space_app.py"]

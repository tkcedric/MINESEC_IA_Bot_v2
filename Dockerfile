# 1. On part d'une image de base Python officielle
FROM python:3.11-slim

# 2. On définit le répertoire de travail à l'intérieur du conteneur
WORKDIR /app

# 3. Installation des dépendances système complètes pour LaTeX
# Installer les dépendances système (LaTeX + polices)
RUN apt-get update && apt-get install -y \
    pandoc \
    texlive-full \
    texlive-fonts-recommended \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-xetex \
    lmodern \
    fonts-liberation \
    fonts-freefont-ttf \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 4. On copie le fichier des dépendances Python et on les installe
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. On copie tout le reste de notre code dans le conteneur
COPY . .

# 6. On expose le port que notre application Flask va utiliser
EXPOSE 10000

# 7. La commande pour lancer notre application
CMD ["python", "bot.py"]
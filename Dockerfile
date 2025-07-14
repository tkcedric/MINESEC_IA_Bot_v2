# 1. On part d'une image officielle qui contient déjà Pandoc et un environnement LaTeX COMPLET.
FROM pandoc/latex:latest

# 2. On installe Python et pip dans cet environnement.
# apk est le gestionnaire de paquets de Alpine Linux, l'OS de cette image.
RUN apk add --no-cache python3 py3-pip

# 3. On met à jour pip et on crée un lien symbolique pour que 'python' pointe vers 'python3'
RUN pip install --upgrade pip
RUN ln -s /usr/bin/python3 /usr/bin/python

# 4. On définit le répertoire de travail
WORKDIR /app

# 5. On copie et on installe nos dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. On copie tout le reste de notre code
COPY . .

# 7. On expose le port pour le health check de Render
EXPOSE 10000

# 8. La commande pour lancer notre application
CMD ["python", "bot.py"]
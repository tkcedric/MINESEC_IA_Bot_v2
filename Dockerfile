# 1. On part d'une image officielle qui contient déjà Pandoc et LaTeX
FROM pandoc/latex:latest

# 2. On installe Python et le module pour les environnements virtuels
RUN apk add --no-cache python3 py3-pip py3-venv

# 3. On crée un environnement virtuel Python à l'intérieur de notre conteneur
RUN python3 -m venv /opt/venv

# 4. On active cet environnement virtuel pour toutes les commandes suivantes
ENV PATH="/opt/venv/bin:$PATH"

# 5. Maintenant qu'on est DANS l'environnement virtuel, on peut utiliser pip sans risque
# On met à jour pip et on installe nos dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. On définit le répertoire de travail et on copie notre code
WORKDIR /app
COPY . .

# 7. On expose le port pour le health check de Render
EXPOSE 10000

# 8. La commande pour lancer notre application
CMD ["python", "bot.py"]
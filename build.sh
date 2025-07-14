#!/usr/bin/env bash
# exit on error
set -o errexit

# Installation des dépendances Python
pip install -r requirements.txt

# Installation des paquets système
apt-get update && apt-get install -y pandoc texlive-xetex --no-install-recommends
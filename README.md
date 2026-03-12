#  Système Distribué de Supervision Réseau

## Description
Système de supervision réseau distribué permettant de surveiller l'état de plusieurs nœuds (machines, VMs, containers) via des agents clients qui envoient périodiquement des métriques à un serveur central.

## Installation sur Kali Linux


# 1. Cloner le projet
git clone https://github.com/Abdouazizciss/SupervisionReseau.git

cd SupervisionReseau

# 2. Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Installer MySQL/MariaDB
sudo apt update

sudo apt install mariadb-server -y

sudo systemctl start mariadb

# 5. Créer la base de données
sudo mysql -u root -p supervision_app.sql

# 6. Lancer le serveur
python run.py serveur

# 7. Lancer un client (dans un autre terminal)
ppython -m src.client.agent_supervision serveur1 localhost

# Lancer un deuxième client (terminal 3)
python -m src.client.agent_supervision serveur2 localhost

# Lancer des clients de test automatiques
python run.py test --clients 10

# Voir les métriques dans la base de données
mysql -u supervision_app -p -e "USE supervision_reseau; SELECT * FROM metriques ORDER BY horodatage DESC LIMIT 5;"
# Mot de passe: supervision123

# Voir les alertes générées
mysql -u supervision_app -p -e "USE supervision_reseau; SELECT * FROM alertes ORDER BY horodatage DESC LIMIT 5;"
```

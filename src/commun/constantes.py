#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module contenant toutes les constantes du projet
Partagé entre le client et le serveur
"""

# ============================================
# CONFIGURATION RÉSEAU
# ============================================

# Port par défaut du serveur
PORT_SERVEUR = 8888

# Timeout de connexion en secondes
TIMEOUT_CONNEXION = 30

# Délai avant de considérer un nœud en panne (en secondes)
DELAI_PANNE = 90

# Taille maximale des messages (en octets)
TAILLE_MAX_MESSAGE = 4096


# ============================================
# FRÉQUENCE D'ENVOI
# ============================================

# Fréquence d'envoi des métriques (en secondes)
FREQUENCE_ENVOI = 30

# Fréquence de vérification des pannes (en secondes)
FREQUENCE_VERIF_PANNE = 30


# ============================================
# SEUILS D'ALERTE
# ============================================

# Seuil d'alerte CPU (%)
SEUIL_CPU = 90.0

# Seuil d'alerte Mémoire (%)
SEUIL_MEMOIRE = 90.0

# Seuil d'alerte Disque (%)
SEUIL_DISQUE = 90.0


# ============================================
# SERVICES SURVEILLÉS
# ============================================

# Services réseau à surveiller
SERVICES_RESEAU = [
    "HTTP",     # Service web
    "HTTPS",    # Service web sécurisé
    "SSH"       # Shell sécurisé
]

# Services applicatifs à surveiller
SERVICES_APPLICATION = [
    "FIREFOX",  # Navigateur Firefox
    "CHROME",   # Navigateur Chrome
    "VSCODE"    # Éditeur VS Code
]

# Liste complète des services
SERVICES_COMPLETS = SERVICES_RESEAU + SERVICES_APPLICATION

# Ports à surveiller
PORTS_SURVEILLES = [
    80,   # HTTP
    443,  # HTTPS
    22,   # SSH
    3306  # MySQL
]


# ============================================
# TYPES DE MESSAGES
# ============================================

# Message d'initialisation (première connexion)
MSG_INIT = "INIT"

# Message de métriques (envoi périodique)
MSG_METRICS = "METRICS"

# Message de commande (serveur -> client)
MSG_COMMANDE = "COMMANDE"

# Message de statut (réponse aux commandes)
MSG_STATUS = "STATUS"

# Message d'alerte
MSG_ALERTE = "ALERTE"


# ============================================
# STATUTS DES SERVICES
# ============================================

STATUT_OK = "OK"
STATUT_DOWN = "DOWN"
STATUT_UNKNOWN = "UNKNOWN"
STATUT_OPEN = "OPEN"
STATUT_CLOSED = "CLOSED"


# ============================================
# CODES DE RETOUR
# ============================================

CODE_SUCCESS = 200
CODE_CREATED = 201
CODE_BAD_REQUEST = 400
CODE_NOT_FOUND = 404
CODE_SERVER_ERROR = 500


# ============================================
# CONFIGURATION BASE DE DONNÉES
# ============================================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'supervision_app',
    'password': 'supervision123',
    'database': 'supervision_reseau',
    'port': 3306
}

DB_POOL_SIZE = 10
DB_MAX_POOL_SIZE = 20


# ============================================
# MESSAGES D'ERREUR
# ============================================

ERREUR_CONNEXION = "Impossible de se connecter au serveur"
ERREUR_ENVOI = "Erreur lors de l'envoi du message"
ERREUR_RECEPTION = "Erreur lors de la réception du message"
ERREUR_FORMAT = "Format de message invalide"
ERREUR_BD = "Erreur de base de données"


# ============================================
# CHEMINS DE FICHIERS
# ============================================

DOSSIER_LOGS = "logs"
FICHIER_LOG = "supervision.log"


# ============================================
# VERSIONS
# ============================================

VERSION_PROJET = "1.0.0"
VERSION_PROTOCOLE = "1.0"

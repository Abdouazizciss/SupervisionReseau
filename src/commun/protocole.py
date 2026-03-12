#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module définissant le protocole de communication
Règles, formats et gestion des erreurs
"""

from enum import Enum
from datetime import datetime
import json
from .constantes import *
from .message import Message

class TypeMessage(Enum):
    """Types de messages échangés"""
    INIT = MSG_INIT
    METRIQUES = MSG_METRICS
    COMMANDE = MSG_COMMANDE
    STATUS = MSG_STATUS
    ALERTE = MSG_ALERTE


class CodeReponse(Enum):
    """Codes de réponse"""
    OK = CODE_SUCCESS
    CREATED = CODE_CREATED
    BAD_REQUEST = CODE_BAD_REQUEST
    NOT_FOUND = CODE_NOT_FOUND
    SERVER_ERROR = CODE_SERVER_ERROR


class Protocole:
    """
    Définition complète du protocole de communication
    
    SPÉCIFICATIONS:
    --------------
    1. FORMAT DES MESSAGES:
       - Tous les messages sont au format JSON
       - Chaque message se termine par un retour à la ligne (\n)
       - Encodage: UTF-8
    
    2. TYPES DE MESSAGES:
       - INIT: Première connexion d'un agent
       - METRICS: Envoi périodique des métriques
       - COMMANDE: Instruction du serveur vers l'agent
       - STATUS: Réponse de l'agent
       - ALERTE: Notification d'alerte
    
    3. FRÉQUENCE D'ENVOI:
       - Métriques: toutes les 30 secondes (configurable)
       - Timeout de connexion: 30 secondes
       - Délai avant panne: 90 secondes sans message
    
    4. GESTION DES ERREURS:
       - Timeout -> reconnexion automatique après 5 secondes
       - Message mal formé -> ignoré avec log
       - Panne détectée -> alerte et mise à jour statut
    """
    
    # Version du protocole
    VERSION = VERSION_PROTOCOLE
    
    @staticmethod
    def valider_message(message):
        """
        Valide la structure d'un message
        
        Args:
            message (dict): Message à valider
            
        Returns:
            tuple: (bool, str) - (est_valide, message_erreur)
        """
        # Vérifier que c'est un dictionnaire
        if not isinstance(message, dict):
            return False, "Le message doit être un dictionnaire"
        
        # Champs obligatoires
        champs_obligatoires = ['type', 'node', 'timestamp']
        for champ in champs_obligatoires:
            if champ not in message:
                return False, f"Champ obligatoire manquant: {champ}"
        
        # Vérifier le type de message
        type_msg = message['type']
        types_valides = [t.value for t in TypeMessage]
        if type_msg not in types_valides:
            return False, f"Type de message invalide: {type_msg}"
        
        # Vérifier le timestamp
        try:
            datetime.fromisoformat(message['timestamp'])
        except:
            return False, "Format de timestamp invalide"
        
        # Validations spécifiques selon le type
        if type_msg == MSG_METRICS:
            # Pour METRICS, vérifier les métriques
            if 'cpu' not in message:
                return False, "Message METRICS doit contenir 'cpu'"
            if 'memory' not in message:
                return False, "Message METRICS doit contenir 'memory'"
            if 'disk' not in message:
                return False, "Message METRICS doit contenir 'disk'"
        
        return True, "Message valide"
    
    @staticmethod
    def formater_message(type_msg, node_id, **donnees):
        """
        Formate un message selon le protocole
        
        Args:
            type_msg (str): Type de message
            node_id (str): Identifiant du nœud
            **donnees: Données supplémentaires
            
        Returns:
            str: Message formaté en JSON
        """
        message = {
            'type': type_msg,
            'node': node_id,
            'timestamp': datetime.now().isoformat(),
            **donnees
        }
        return json.dumps(message, ensure_ascii=False) + '\n'
    
    @staticmethod
    def parser_message(data):
        """
        Parse un message reçu
        
        Args:
            data (str): Données brutes reçues
            
        Returns:
            Message: Instance de Message ou None si erreur
        """
        try:
            # Nettoyer les données
            data = data.strip()
            if not data:
                return None
            
            # Parser le JSON
            msg_dict = json.loads(data)
            
            # Valider
            valide, erreur = Protocole.valider_message(msg_dict)
            if not valide:
                print(f"⚠ Message invalide: {erreur}")
                return None
            
            # Convertir en objet Message
            return Message.from_json(data)
            
        except json.JSONDecodeError as e:
            print(f"⚠ Erreur de parsing JSON: {e}")
            return None
        except Exception as e:
            print(f"⚠ Erreur inattendue: {e}")
            return None
    
    @staticmethod
    def est_une_panne(dernier_message, maintenant, delai=DELAI_PANNE):
        """
        Détermine si un nœud est en panne
        
        Args:
            dernier_message (datetime): Date du dernier message reçu
            maintenant (datetime): Date actuelle
            delai (int): Délai avant panne en secondes
            
        Returns:
            bool: True si le nœud est considéré en panne
        """
        if not dernier_message:
            return True
        
        duree_inactivite = (maintenant - dernier_message).total_seconds()
        return duree_inactivite > delai
    
    @staticmethod
    def creer_reponse(code, message=""):
        """
        Crée un message de réponse standard
        
        Args:
            code (CodeReponse): Code de réponse
            message (str): Message explicatif
            
        Returns:
            dict: Message de réponse
        """
        return {
            'type': MSG_STATUS,
            'code': code.value if isinstance(code, CodeReponse) else code,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def creer_commande(node_id, commande, **params):
        """
        Crée une commande pour un agent
        
        Args:
            node_id (str): Identifiant du nœud destinataire
            commande (str): Commande à exécuter
            **params: Paramètres de la commande
            
        Returns:
            str: Commande formatée
        """
        return Protocole.formater_message(
            MSG_COMMANDE,
            node_id,
            commande=commande,
            params=params
        )


# ============================================
# EXEMPLES D'UTILISATION
# ============================================

"""
EXEMPLE 1: Message d'initialisation
{
    "type": "INIT",
    "node": "serveur1",
    "timestamp": "2024-01-15T10:30:00",
    "os": "Windows",
    "processeur": "Intel64",
    "hostname": "PC-001"
}

EXEMPLE 2: Message de métriques
{
    "type": "METRICS",
    "node": "serveur1",
    "timestamp": "2024-01-15T10:30:30",
    "cpu": 45.2,
    "memory": 62.5,
    "disk": 38.7,
    "uptime": 3600,
    "services": {
        "HTTP": "OK",
        "HTTPS": "OK",
        "SSH": "OK",
        "FIREFOX": "OK",
        "CHROME": "DOWN",
        "VSCODE": "OK"
    },
    "ports": {
        "80": "OPEN",
        "443": "OPEN",
        "22": "OPEN",
        "3306": "CLOSED"
    }
}

EXEMPLE 3: Commande
{
    "type": "COMMANDE",
    "node": "serveur1",
    "timestamp": "2024-01-15T10:31:00",
    "commande": "UP",
    "params": {
        "service": "HTTP"
    }
}

EXEMPLE 4: Statut
{
    "type": "STATUS",
    "node": "serveur1",
    "timestamp": "2024-01-15T10:31:05",
    "statut": "OK",
    "code": 200,
    "message": "Service HTTP activé"
}
"""


# ============================================
# TESTS RAPIDES (si exécuté directement)
# ============================================

if __name__ == "__main__":
    print("🧪 Test du module protocole")
    print("="*50)
    
    # Tester la validation
    msg_test = {
        'type': 'METRICS',
        'node': 'test1',
        'timestamp': datetime.now().isoformat(),
        'cpu': 45.2,
        'memory': 62.5,
        'disk': 38.7
    }
    
    valide, msg = Protocole.valider_message(msg_test)
    print(f"Validation: {valide} - {msg}")
    
    # Tester le formatage
    cmd = Protocole.creer_commande('test1', 'UP', service='HTTP')
    print(f"Commande formatée: {cmd}")
    
    print("="*50)
    print("✅ Tests terminés")
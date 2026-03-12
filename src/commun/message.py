#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module définissant la structure des messages échangés entre client et serveur
Format: JSON avec timestamp et type de message
"""

import json
from datetime import datetime
from .constantes import *

class Message:
    """
    Classe représentant un message échangé entre client et serveur
    
    Format JSON:
    {
        "node": "serveur1",
        "timestamp": "2024-01-15T10:30:00",
        "type": "METRICS",
        "cpu": 45.2,
        "memory": 62.5,
        "disk": 38.7,
        "uptime": 3600,
        "services": {
            "HTTP": "OK",
            "HTTPS": "OK",
            "SSH": "OK",
            "FIREFOX": "OK",
            "CHROME": "OK",
            "VSCODE": "OK"
        },
        "ports": {
            "80": "OPEN",
            "443": "OPEN", 
            "22": "OPEN",
            "3306": "OPEN"
        }
    }
    """
    
    def __init__(self):
        """Initialise un message vide"""
        self.node_id = None              # Identifiant du nœud
        self.horodatage = datetime.now() # Date et heure du message
        self.type_message = None          # Type de message (INIT, METRICS, etc.)
        
        # Métriques système
        self.charge_cpu = 0.0             # Charge CPU en %
        self.charge_memoire = 0.0         # Charge mémoire en %
        self.stockage_disk = 0.0          # Utilisation disque en %
        self.uptime = 0                   # Temps d'activité en secondes
        
        # Statuts des services et ports
        self.services = {}                 # Dictionnaire {nom_service: statut}
        self.ports = {}                    # Dictionnaire {port: statut}
        
        # Informations supplémentaires (pour l'initialisation, etc.)
        self.infos_supplementaires = {}
    
    def to_json(self):
        """
        Convertit le message en format JSON
        
        Returns:
            str: Représentation JSON du message
        """
        message = {
            'node': self.node_id,
            'timestamp': self.horodatage.isoformat(),
            'type': self.type_message,
            'cpu': self.charge_cpu,
            'memory': self.charge_memoire,
            'disk': self.stockage_disk,
            'uptime': self.uptime,
            'services': self.services,
            'ports': self.ports
        }
        
        # Ajouter les informations supplémentaires
        if self.infos_supplementaires:
            message.update(self.infos_supplementaires)
        
        return json.dumps(message, ensure_ascii=False, indent=None)
    
    @classmethod
    def from_json(cls, json_str):
        """
        Crée un message à partir d'une chaîne JSON
        
        Args:
            json_str (str): Chaîne JSON représentant un message
            
        Returns:
            Message: Instance de Message ou None si erreur
        """
        try:
            data = json.loads(json_str)
            msg = cls()
            
            # Informations de base
            msg.node_id = data.get('node')
            msg.type_message = data.get('type')
            
            # Timestamp
            if 'timestamp' in data:
                try:
                    msg.horodatage = datetime.fromisoformat(data['timestamp'])
                except:
                    msg.horodatage = datetime.now()
            
            # Métriques (avec conversion de type sécurisée)
            try:
                msg.charge_cpu = float(data.get('cpu', 0.0))
            except (TypeError, ValueError):
                msg.charge_cpu = 0.0
                
            try:
                msg.charge_memoire = float(data.get('memory', 0.0))
            except (TypeError, ValueError):
                msg.charge_memoire = 0.0
                
            try:
                msg.stockage_disk = float(data.get('disk', 0.0))
            except (TypeError, ValueError):
                msg.stockage_disk = 0.0
                
            try:
                msg.uptime = int(data.get('uptime', 0))
            except (TypeError, ValueError):
                msg.uptime = 0
            
            # Services et ports
            msg.services = data.get('services', {})
            msg.ports = data.get('ports', {})
            
            # Informations supplémentaires (tout ce qui n'est pas dans les clés standard)
            cles_standard = {'node', 'timestamp', 'type', 'cpu', 'memory', 
                            'disk', 'uptime', 'services', 'ports'}
            for key, value in data.items():
                if key not in cles_standard:
                    msg.infos_supplementaires[key] = value
            
            return msg
            
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de parsing JSON: {e}")
            return None
        except Exception as e:
            print(f"❌ Erreur lors de la création du message: {e}")
            return None
    
    def est_valide(self):
        """
        Vérifie si le message est valide
        
        Returns:
            bool: True si le message est valide, False sinon
        """
        if not self.node_id:
            return False
        if not self.type_message:
            return False
        if self.type_message not in [MSG_INIT, MSG_METRICS, MSG_COMMANDE, MSG_STATUS, MSG_ALERTE]:
            return False
        return True
    
    def __str__(self):
        """Représentation lisible du message"""
        return f"Message[{self.type_message}] de {self.node_id} à {self.horodatage.strftime('%H:%M:%S')}"
    
    def __repr__(self):
        """Représentation détaillée"""
        return self.to_json()


# ============================================
# FONCTIONS UTILITAIRES POUR CRÉER DES MESSAGES
# ============================================

def creer_message_init(node_id, infos_systeme):
    """
    Crée un message d'initialisation
    
    Args:
        node_id (str): Identifiant du nœud
        infos_systeme (dict): Informations système
        
    Returns:
        Message: Message d'initialisation
    """
    msg = Message()
    msg.node_id = node_id
    msg.type_message = MSG_INIT
    msg.infos_supplementaires = infos_systeme
    return msg


def creer_message_metriques(node_id, cpu, memoire, disque, uptime, services, ports):
    """
    Crée un message de métriques
    
    Args:
        node_id (str): Identifiant du nœud
        cpu (float): Charge CPU
        memoire (float): Charge mémoire
        disque (float): Utilisation disque
        uptime (int): Temps d'activité
        services (dict): Statuts des services
        ports (dict): Statuts des ports
        
    Returns:
        Message: Message de métriques
    """
    msg = Message()
    msg.node_id = node_id
    msg.type_message = MSG_METRICS
    msg.charge_cpu = cpu
    msg.charge_memoire = memoire
    msg.stockage_disk = disque
    msg.uptime = uptime
    msg.services = services
    msg.ports = ports
    return msg


def creer_commande(node_id, commande, **params):
    """
    Crée un message de commande
    
    Args:
        node_id (str): Identifiant du nœud destinataire
        commande (str): Commande à exécuter
        **params: Paramètres de la commande
        
    Returns:
        Message: Message de commande
    """
    msg = Message()
    msg.node_id = node_id
    msg.type_message = MSG_COMMANDE
    msg.infos_supplementaires = {
        'commande': commande,
        'params': params
    }
    return msg


def creer_message_statut(node_id, statut, **infos):
    """
    Crée un message de statut
    
    Args:
        node_id (str): Identifiant du nœud
        statut (str): Statut (OK, ERROR, etc.)
        **infos: Informations supplémentaires
        
    Returns:
        Message: Message de statut
    """
    msg = Message()
    msg.node_id = node_id
    msg.type_message = MSG_STATUS
    msg.infos_supplementaires = {
        'statut': statut,
        **infos
    }
    return msg
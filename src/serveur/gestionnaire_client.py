#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de connexion client
"""

import threading
import json
import socket
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from commun.message import Message
from commun.constantes import *

class GestionnaireClient:
    """Gère la communication avec un client"""
    
    def __init__(self, client_socket, address, db_manager, serveur):
        self.socket = client_socket
        self.address = address
        self.db_manager = db_manager
        self.serveur = serveur
        self.node_id = None
        self.derniere_activite = datetime.now()
        self.running = True
        self.logger = serveur.logger
        
        self.infos_noeud = {}
        
    def demarrer(self):
        """Démarre la gestion du client"""
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
    
    def run(self):
        """Boucle principale de traitement"""
        buffer = ""
        
        try:
            self.socket.settimeout(30)
            self.logger.info(f"👤 Nouveau client connecté: {self.address}")
            
            while self.running:
                try:
                    data = self.socket.recv(4096).decode('utf-8')
                    if not data:
                        break
                    
                    buffer += data
                    while '\n' in buffer:
                        ligne, buffer = buffer.split('\n', 1)
                        self.traiter_message(ligne)
                        self.derniere_activite = datetime.now()
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"Erreur avec le client {self.node_id}: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Erreur de connexion: {e}")
        finally:
            self.fermer()
    
    def traiter_message(self, ligne):
        """Traite un message reçu"""
        message = Message.from_json(ligne)
        if not message:
            return
        
        self.logger.debug(f"📨 Message reçu de {message.node_id}: {message.type_message}")
        
        if message.type_message == "INIT":
            self.traiter_initialisation(message)
        elif message.type_message == "METRICS":
            self.traiter_metriques(message)
        elif message.type_message == "STATUS":
            self.traiter_statut(message)
    
    def traiter_initialisation(self, message):
        """Traite un message d'initialisation"""
        self.node_id = message.node_id
        self.infos_noeud = message.infos_supplementaires
        
        # Enregistrer le nœud dans la base de données
        if self.db_manager:
            self.db_manager.enregistrer_noeud(self.node_id, self.infos_noeud)
        
        # Enregistrer le client auprès du serveur
        self.serveur.enregistrer_client(self.node_id, self)
        
        self.logger.info(f"✅ Nouveau nœud enregistré: {self.node_id} depuis {self.address}")
    
    def traiter_metriques(self, message):
        """Traite un message de métriques"""
        # Afficher les métriques reçues
        print(f"📊 {self.node_id} - CPU:{message.charge_cpu}% MEM:{message.charge_memoire}%")
        
        # Vérifier les seuils d'alerte
        self.verifier_seuils(message)
        
        # Sauvegarder dans la base de données
        if self.db_manager:
            self.db_manager.sauvegarder_metriques(
                self.node_id,
                message.charge_cpu,
                message.charge_memoire,
                message.stockage_disk,
                message.uptime
            )
            self.db_manager.mettre_a_jour_connexion(self.node_id)
    
    def traiter_statut(self, message):
        """Traite un message de statut"""
        self.logger.debug(f"Statut reçu de {self.node_id}: {message.infos_supplementaires}")
    
    def verifier_seuils(self, message):
        """Vérifie si les seuils d'alerte sont dépassés"""
        if message.charge_cpu > 90:
            self.logger.alerte(f"CPU > 90% sur {self.node_id}: {message.charge_cpu}%")
            if self.db_manager:
                self.db_manager.enregistrer_alerte(
                    self.node_id, 'cpu', message.charge_cpu, 90
                )
        
        if message.charge_memoire > 90:
            self.logger.alerte(f"Mémoire > 90% sur {self.node_id}: {message.charge_memoire}%")
            if self.db_manager:
                self.db_manager.enregistrer_alerte(
                    self.node_id, 'memoire', message.charge_memoire, 90
                )
        
        if message.stockage_disk > 90:
            self.logger.alerte(f"Disque > 90% sur {self.node_id}: {message.stockage_disk}%")
            if self.db_manager:
                self.db_manager.enregistrer_alerte(
                    self.node_id, 'disque', message.stockage_disk, 90
                )
    
    def envoyer_commande(self, commande, **params):
        """Envoie une commande au client"""
        try:
            message = {
                'type': commande,
                **params,
                'timestamp': datetime.now().isoformat()
            }
            data = json.dumps(message) + '\n'
            self.socket.send(data.encode('utf-8'))
            self.logger.info(f"📤 Commande envoyée à {self.node_id}: {commande}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur envoi commande à {self.node_id}: {e}")
            return False
    
    def fermer(self):
        """Ferme la connexion avec le client"""
        self.running = False
        try:
            if self.socket:
                self.socket.close()
        except:
            pass
        
        if self.node_id:
            self.serveur.retirer_client(self.node_id)
            self.logger.info(f"👋 Client déconnecté: {self.node_id}")
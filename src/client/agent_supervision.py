#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Agent de supervision (client)
"""

import socket
import threading
import time
import json
import sys
import signal
import random
from datetime import datetime

# Importer les modules du projet
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from commun.message import Message
from commun.constantes import *
from .simulateur_metriques import SimulateurMetriques

# Tentative d'import du collecteur réel (optionnel)
try:
    from .collecteur_metriques import CollecteurMetriques
    COLLECTEUR_REEL_DISPONIBLE = True
except ImportError:
    COLLECTEUR_REEL_DISPONIBLE = False
    print("Note: collecteur réel non disponible, utilisation du simulateur")

class AgentSupervision:
    """Agent de supervision s'exécutant sur chaque nœud"""
    
    def __init__(self, node_id, serveur_address='localhost', port=8888, mode='simulation'):
        self.node_id = node_id
        self.serveur_address = serveur_address
        self.port = port
        self.mode = mode
        
        # Choisir le collecteur (simulation ou réel)
        if mode == 'reel' and COLLECTEUR_REEL_DISPONIBLE:
            try:
                self.collecteur = CollecteurMetriques(node_id)
                print(f"✓ Mode réel activé pour {node_id}")
            except:
                self.collecteur = SimulateurMetriques(node_id)
                print(f"⚠ Mode réel indisponible, utilisation simulation pour {node_id}")
        else:
            self.collecteur = SimulateurMetriques(node_id)
            print(f"✓ Mode simulation pour {node_id}")
        
        self.socket = None
        self.connected = False
        self.running = True
        self.en_panne = False
        
        # Threads
        self.thread_envoi = None
        self.thread_ecoute = None
        self.lock = threading.Lock()
        
    def connecter(self):
        """Établit la connexion avec le serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)  # 30 secondes de timeout
            self.socket.connect((self.serveur_address, self.port))
            self.connected = True
            print(f"✓ Connecté au serveur {self.serveur_address}:{self.port}")
            
            # Envoyer les informations initiales
            self.envoyer_informations_initiales()
            
            return True
        except Exception as e:
            print(f"✗ Erreur de connexion: {e}")
            return False
    
    def envoyer_informations_initiales(self):
        """Envoie les informations système au serveur"""
        message = Message()
        message.node_id = self.node_id
        message.type_message = "INIT"
        message.infos_supplementaires = self.collecteur.get_infos_systeme()
        
        self.envoyer_message(message)
        print(f"✓ Informations initiales envoyées pour {self.node_id}")
    
    def envoyer_metriques(self):
        """Collecte et envoie les métriques au serveur"""
        try:
            message = Message()
            message.node_id = self.node_id
            message.type_message = "METRICS"
            
            # Collecter les métriques selon le mode
            if self.mode == 'reel' and COLLECTEUR_REEL_DISPONIBLE:
                message.charge_cpu = self.collecteur.get_charge_cpu()
                message.charge_memoire = self.collecteur.get_charge_memoire()
                message.stockage_disk = self.collecteur.get_stockage_disk()
                message.services = self.collecteur.get_statuts_services()
                message.ports = self.collecteur.get_statuts_ports()
            else:
                message.charge_cpu = self.collecteur.simuler_charge_cpu()
                message.charge_memoire = self.collecteur.simuler_charge_memoire()
                message.stockage_disk = self.collecteur.simuler_stockage_disk()
                message.services = self.collecteur.simuler_statuts_services()
                message.ports = self.collecteur.simuler_statuts_ports()
            
            message.uptime = self.collecteur.get_uptime()
            
            self.envoyer_message(message)
            print(f"📊 Métriques envoyées: CPU={message.charge_cpu}%, MEM={message.charge_memoire}%")
            
            # Simuler une panne aléatoire (pour les tests)
            if not self.en_panne and random.random() < 0.01:  # 1% de chance
                self.simuler_panne()
                
        except Exception as e:
            print(f"✗ Erreur lors de l'envoi des métriques: {e}")
            self.reconnecter()
    
    def envoyer_message(self, message):
        """Envoie un message au serveur"""
        with self.lock:
            try:
                if self.socket and self.connected:
                    data = message.to_json() + '\n'
                    self.socket.send(data.encode('utf-8'))
            except Exception as e:
                print(f"✗ Erreur d'envoi: {e}")
                self.connected = False
    
    def ecouter_commandes(self):
        """Écoute les commandes du serveur"""
        buffer = ""
        while self.running and self.connected:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                while '\n' in buffer:
                    ligne, buffer = buffer.split('\n', 1)
                    self.traiter_commande(ligne)
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"✗ Erreur de réception: {e}")
                break
        
        if self.running:
            self.reconnecter()
    
    def traiter_commande(self, commande_json):
        """Traite une commande reçue du serveur"""
        try:
            commande = json.loads(commande_json)
            print(f"📨 Commande reçue: {commande}")
            
            if commande.get('type') == 'UP':
                service = commande.get('service')
                self.activer_service(service)
            elif commande.get('type') == 'STATUS':
                self.envoyer_statut()
                
        except json.JSONDecodeError:
            print(f"⚠ Commande mal formatée: {commande_json}")
    
    def activer_service(self, service):
        """Active un service sur le nœud"""
        print(f"🔧 Activation du service: {service}")
        # Logique d'activation du service
        # Dans une implémentation réelle, ici on lancerait le service
        # Par exemple: subprocess.run(['systemctl', 'start', service.lower()])
    
    def envoyer_statut(self):
        """Envoie le statut actuel au serveur"""
        message = Message()
        message.node_id = self.node_id
        message.type_message = "STATUS"
        message.infos_supplementaires = {'status': 'OK', 'uptime': self.collecteur.get_uptime()}
        self.envoyer_message(message)
        print(f"✓ Statut envoyé au serveur")
    
    def simuler_panne(self):
        """Simule une panne du nœud pour les tests"""
        print("⚠⚠⚠ SIMULATION DE PANNE ⚠⚠⚠")
        self.en_panne = True
        self.connected = False
        
        if self.socket:
            self.socket.close()
        
        # Simuler une panne de 10 secondes
        for i in range(10, 0, -1):
            print(f"⏱ Panne: reconnexion dans {i} secondes...")
            time.sleep(1)
        
        self.en_panne = False
        print("🔄 Tentative de reconnexion...")
        self.reconnecter()
    
    def reconnecter(self):
        """Tente de se reconnecter au serveur"""
        tentatives = 0
        while self.running and not self.connected:
            tentatives += 1
            print(f"🔄 Tentative de reconnexion #{tentatives}...")
            if self.connecter():
                print("✓ Reconnexion réussie !")
                # Envoyer un statut immédiatement
                self.envoyer_statut()
                break
            time.sleep(5)
    
    def demarrer(self):
        """Démarre l'agent de supervision"""
        print(f"\n{'='*50}")
        print(f"🚀 Démarrage de l'agent {self.node_id}")
        print(f"📡 Serveur: {self.serveur_address}:{self.port}")
        print(f"⚙ Mode: {self.mode}")
        print(f"{'='*50}\n")
        
        # Connexion au serveur
        if not self.connecter():
            print("❌ Impossible de se connecter au serveur")
            return
        
        # Thread d'envoi périodique des métriques
        def boucle_envoi():
            while self.running:
                if self.connected:
                    self.envoyer_metriques()
                time.sleep(30)  # Envoi toutes les 30 secondes
        
        self.thread_envoi = threading.Thread(target=boucle_envoi)
        self.thread_envoi.daemon = True
        self.thread_envoi.start()
        
        # Thread d'écoute des commandes
        self.thread_ecoute = threading.Thread(target=self.ecouter_commandes)
        self.thread_ecoute.daemon = True
        self.thread_ecoute.start()
        
        print(f"✅ Agent {self.node_id} en cours d'exécution...")
        print(f"📝 Tapez Ctrl+C pour arrêter\n")
        
        # Maintenir le thread principal en vie
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.arreter()
    
    def arreter(self):
        """Arrête l'agent"""
        print(f"\n🛑 Arrêt de l'agent {self.node_id}...")
        self.running = False
        if self.socket:
            self.socket.close()
        print(f"👋 Agent {self.node_id} arrêté")

def main():
    """Point d'entrée principal"""
    if len(sys.argv) < 2:
        print("\n" + "="*50)
        print("📋 Utilisation: python agent_supervision.py <node_id> [serveur_address] [mode]")
        print("="*50)
        print("Exemples:")
        print("  python agent_supervision.py server1              # Mode simulation")
        print("  python agent_supervision.py server1 localhost    # Mode simulation")
        print("  python agent_supervision.py server1 localhost simulation")
        print("  python agent_supervision.py server1 localhost reel")
        print("\nModes disponibles:")
        print("  simulation - Données simulées (défaut)")
        print("  reel      - Métriques réelles (nécessite psutil)")
        print("="*50 + "\n")
        sys.exit(1)
    
    node_id = sys.argv[1]
    serveur_address = sys.argv[2] if len(sys.argv) > 2 else 'localhost'
    mode = sys.argv[3] if len(sys.argv) > 3 else 'simulation'
    
    agent = AgentSupervision(node_id, serveur_address, mode=mode)
    
    # Gestionnaire de signal pour l'arrêt propre
    def signal_handler(sig, frame):
        agent.arreter()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    agent.demarrer()

if __name__ == "__main__":
    main()
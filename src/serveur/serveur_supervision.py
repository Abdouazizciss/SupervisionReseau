#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Serveur de supervision principal
"""

import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from commun.constantes import *
from .gestionnaire_client import GestionnaireClient
from .journalisation import Journalisation
from .interface_console import InterfaceConsole

# Tentative d'import de la base de données (optionnel)
try:
    from database.database_manager import DatabaseManager
    DB_DISPONIBLE = True
except ImportError:
    DB_DISPONIBLE = False
    print("⚠ Module base de données non disponible")

class ServeurSupervision:
    """Serveur de supervision central"""
    
    def __init__(self, port=8888):
        self.port = port
        self.running = True
        self.logger = Journalisation()
        self.date_demarrage = datetime.now()
        
        # Initialiser la base de données si disponible
        if DB_DISPONIBLE:
            try:
                self.db_manager = DatabaseManager()
                self.logger.info("✅ Connexion à la base de données établie")
            except Exception as e:
                self.logger.error(f"❌ Erreur BD: {e}")
                self.db_manager = None
        else:
            self.db_manager = None
            self.logger.warning("⚠ Mode sans base de données (les métriques ne seront pas sauvegardées)")
        
        self.clients_actifs = {}  # node_id -> GestionnaireClient
        self.lock_clients = threading.Lock()
        
        # Choix du pool de threads
        # ThreadPoolExecutor est l'équivalent Python de FixedThreadPool
        self.thread_pool = self.choisir_pool_threads()
        
        self.interface = InterfaceConsole(self)
        
    def choisir_pool_threads(self):
        """
        Comparaison des différents types de pools en Python:
        - ThreadPoolExecutor: Nombre fixe de threads, bon contrôle
        - On utilise un nombre basé sur le nombre de CPUs * 2 pour les opérations I/O
        """
        import os
        nb_coeurs = os.cpu_count() or 4
        taille_pool = nb_coeurs * 2
        
        self.logger.info(f"⚙️  Création d'un ThreadPoolExecutor de taille: {taille_pool}")
        return ThreadPoolExecutor(max_workers=taille_pool)
    
    def demarrer(self):
        """Démarre le serveur"""
        try:
            self.socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_serveur.bind(('', self.port))
            self.socket_serveur.listen(100)  # File d'attente de 100 connexions
            self.socket_serveur.settimeout(1.0)  # Timeout pour vérifier running
            
            self.logger.info(f"🚀 Serveur de supervision démarré sur le port {self.port}")
            self.logger.info(f"📅 Date de démarrage: {self.date_demarrage.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Démarrer l'interface console
            self.interface.demarrer()
            
            # Démarrer le thread de surveillance des nœuds inactifs
            self.thread_surveillance = threading.Thread(target=self.surveiller_noeuds)
            self.thread_surveillance.daemon = True
            self.thread_surveillance.start()
            
            # Boucle principale d'acceptation
            self.logger.info("👂 En attente de connexions...")
            while self.running:
                try:
                    client_socket, address = self.socket_serveur.accept()
                    self.logger.info(f"📞 Nouvelle connexion de {address}")
                    
                    # Créer un gestionnaire pour ce client
                    gestionnaire = GestionnaireClient(client_socket, address, self.db_manager, self)
                    
                    # Soumettre au pool de threads
                    self.thread_pool.submit(gestionnaire.demarrer)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"❌ Erreur d'acceptation: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du démarrage: {e}")
        finally:
            self.arreter()
    
    def enregistrer_client(self, node_id, gestionnaire):
        """Enregistre un client actif"""
        with self.lock_clients:
            self.clients_actifs[node_id] = gestionnaire
            self.logger.info(f"📝 Client enregistré: {node_id} (total: {len(self.clients_actifs)})")
    
    def retirer_client(self, node_id):
        """Retire un client de la liste des actifs"""
        with self.lock_clients:
            if node_id in self.clients_actifs:
                del self.clients_actifs[node_id]
                self.logger.info(f"🗑️ Client retiré: {node_id} (total: {len(self.clients_actifs)})")
    
    def surveiller_noeuds(self):
        """Surveille les nœuds inactifs et détecte les pannes"""
        while self.running:
            try:
                maintenant = datetime.now()
                noeuds_panne = []
                
                with self.lock_clients:
                    for node_id, client in self.clients_actifs.items():
                        temps_inactif = (maintenant - client.derniere_activite).total_seconds()
                        
                        if temps_inactif > 90:  # 90 secondes sans activité
                            noeuds_panne.append(node_id)
                            self.logger.alerte(
                                f"⛔ Nœud en panne détecté: {node_id} "
                                f"(inactif depuis {temps_inactif:.0f} secondes)"
                            )
                            
                            # Enregistrer dans la base de données
                            if self.db_manager:
                                self.db_manager.enregistrer_alerte(
                                    node_id, 'panne', temps_inactif, 90
                                )
                                self.db_manager.mettre_a_jour_statut_noeud(node_id, 'panne')
                
                # Nettoyer les nœuds en panne
                for node_id in noeuds_panne:
                    self.retirer_client(node_id)
                
                time.sleep(30)  # Vérifier toutes les 30 secondes
                
            except Exception as e:
                self.logger.error(f"❌ Erreur dans la surveillance: {e}")
                time.sleep(30)
    
    def arreter(self):
        """Arrête le serveur"""
        self.logger.info("🛑 Arrêt du serveur...")
        self.running = False
        
        # Fermer toutes les connexions clients
        with self.lock_clients:
            for node_id, client in list(self.clients_actifs.items()):
                client.fermer()
            self.clients_actifs.clear()
        
        # Fermer le socket serveur
        if hasattr(self, 'socket_serveur'):
            try:
                self.socket_serveur.close()
            except:
                pass
        
        # Arrêter le pool de threads
        self.thread_pool.shutdown(wait=False)
        
        # Fermer la connexion à la base de données
        if self.db_manager:
            self.db_manager.fermer()
        
        self.logger.info("👋 Serveur arrêté")

def main():
    """Point d'entrée principal"""
    import sys
    
    port = 8888
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            pass
    
    print("\n" + "═"*60)
    print("🌟 SERVEUR DE SUPERVISION RÉSEAU")
    print("═"*60)
    print(f"📡 Démarrage sur le port {port}...")
    print("💡 Tapez 'aide' pour voir les commandes disponibles")
    print("═"*60 + "\n")
    
    serveur = ServeurSupervision(port)
    
    try:
        serveur.demarrer()
    except KeyboardInterrupt:
        serveur.arreter()

if __name__ == "__main__":
    main()
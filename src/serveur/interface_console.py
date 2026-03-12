#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interface console du serveur
"""

import threading
import sys
from datetime import datetime

class InterfaceConsole:
    """Interface en ligne de commande pour le serveur"""
    
    def __init__(self, serveur):
        self.serveur = serveur
        self.running = True
        self.logger = serveur.logger
        
    def demarrer(self):
        """Démarre l'interface console dans un thread séparé"""
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
    
    def run(self):
        """Boucle principale de l'interface"""
        self.afficher_aide()
        
        while self.running:
            try:
                commande = input("\n🔷 supervision> ").strip().lower()
                self.traiter_commande(commande)
            except EOFError:
                break
            except KeyboardInterrupt:
                self.serveur.arreter()
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def traiter_commande(self, commande):
        """Traite une commande utilisateur"""
        if not commande:
            return
        
        parts = commande.split()
        cmd = parts[0]
        
        if cmd in ['aide', 'help', '?']:
            self.afficher_aide()
        
        elif cmd in ['liste', 'list', 'ls']:
            self.lister_noeuds()
        
        elif cmd == 'infos':
            if len(parts) > 1:
                self.afficher_infos_noeud(parts[1])
            else:
                print("📋 Usage: infos <node_id>")
        
        elif cmd == 'up':
            if len(parts) > 2:
                self.activer_service(parts[1], ' '.join(parts[2:]))
            else:
                print("📋 Usage: up <node_id> <service>")
        
        elif cmd in ['alerte', 'alertes']:
            self.afficher_alertes()
        
        elif cmd == 'stats':
            self.afficher_statistiques()
        
        elif cmd == 'test':
            self.generer_clients_test()
        
        elif cmd in ['quit', 'exit', 'q']:
            print("👋 Arrêt du serveur...")
            self.serveur.arreter()
        
        else:
            print(f"❌ Commande inconnue: {cmd}")
            print("💡 Tapez 'aide' pour voir les commandes disponibles")
    
    def afficher_aide(self):
        """Affiche l'aide"""
        print("\n" + "═"*60)
        print("🌟 INTERFACE DE SUPERVISION - COMMANDES DISPONIBLES")
        print("═"*60)
        print("📋 Commandes de base:")
        print("  liste, ls              - Liste tous les nœuds actifs")
        print("  infos <node_id>        - Affiche les informations d'un nœud")
        print("  up <node_id> <service> - Active un service sur un nœud")
        print("  alertes                - Affiche les dernières alertes")
        print("  stats                  - Affiche les statistiques")
        print("  test                   - Génère des clients de test")
        print("  aide, help             - Affiche cette aide")
        print("  quit, exit              - Quitte l'application")
        print("═"*60)
    
    def lister_noeuds(self):
        """Liste tous les nœuds actifs"""
        clients = self.serveur.clients_actifs
        
        if not clients:
            print("\n📭 Aucun nœud actif")
            return
        
        print("\n" + "═"*70)
        print(f"📊 NŒUDS ACTIFS ({len(clients)})")
        print("═"*70)
        print(f"{'🆔 Node ID':<20} {'⏱ Dernière activité':<20} {'🌐 Adresse':<20} {'📊 Métriques':<10}")
        print("─"*70)
        
        for node_id, client in clients.items():
            # Récupérer les dernières métriques si disponibles
            metrics = "?"
            print(f"{node_id:<20} {client.derniere_activite.strftime('%H:%M:%S'):<20} {client.address[0]:<20} {metrics:<10}")
    
    def afficher_infos_noeud(self, node_id):
        """Affiche les informations détaillées d'un nœud"""
        if node_id in self.serveur.clients_actifs:
            client = self.serveur.clients_actifs[node_id]
            print(f"\n{'═'*50}")
            print(f"📌 INFORMATIONS DU NŒUD: {node_id}")
            print(f"{'═'*50}")
            print(f"📍 Adresse: {client.address[0]}:{client.address[1]}")
            print(f"⏱ Dernière activité: {client.derniere_activite.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📊 Informations système: {client.infos_noeud}")
            print(f"{'═'*50}")
        else:
            print(f"❌ Nœud {node_id} non trouvé ou inactif")
            print("   Nœuds actifs:", list(self.serveur.clients_actifs.keys()))
    
    def activer_service(self, node_id, service):
        """Active un service sur un nœud"""
        if node_id in self.serveur.clients_actifs:
            client = self.serveur.clients_actifs[node_id]
            if client.envoyer_commande('UP', service=service):
                print(f"✅ Commande d'activation envoyée à {node_id} pour le service {service}")
            else:
                print(f"❌ Échec de l'envoi de la commande à {node_id}")
        else:
            print(f"❌ Nœud {node_id} non trouvé ou inactif")
    
    def afficher_alertes(self):
        """Affiche les dernières alertes"""
        if self.serveur.db_manager:
            alertes = self.serveur.db_manager.get_dernieres_alertes(10)
            print("\n" + "═"*60)
            print("🚨 DERNIÈRES ALERTES")
            print("═"*60)
            print(alertes)
        else:
            print("⚠ Base de données non disponible")
    
    def afficher_statistiques(self):
        """Affiche les statistiques du serveur"""
        nb_noeuds = len(self.serveur.clients_actifs)
        
        print("\n" + "═"*60)
        print("📊 STATISTIQUES DU SERVEUR")
        print("═"*60)
        print(f"🖥️  Serveur démarré depuis: {self.serveur.date_demarrage.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📡 Port d'écoute: {self.serveur.port}")
        print(f"👥 Nœuds actifs: {nb_noeuds}")
        print(f"⚙️  Pool de threads: {self.serveur.thread_pool._max_workers} threads")
        
        if self.serveur.db_manager:
            stats = self.serveur.db_manager.get_statistiques()
            print(stats)
    
    def generer_clients_test(self):
        """Génère des clients de test pour simuler une charge"""
        import subprocess
        import sys
        
        print("🧪 Génération de clients de test...")
        for i in range(1, 4):
            node_id = f"test{i}"
            print(f"  Lancement de {node_id}...")
            if sys.platform == "win32":
                subprocess.Popen([
                    "python", "run.py", "client", node_id, "localhost"
                ], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([
                    "python", "run.py", "client", node_id, "localhost"
                ])
        print("✅ 3 clients de test lancés")
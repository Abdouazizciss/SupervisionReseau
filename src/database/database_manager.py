#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de base de données
Fournit toutes les opérations nécessaires pour le serveur de supervision
"""

import mysql.connector
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from commun.constantes import *
from .connection_pool import ConnectionPool
from serveur.journalisation import Journalisation

class DatabaseManager:
    """
    Gestionnaire des opérations sur la base de données
    
    Ce manager utilise le pool de connexions pour toutes les opérations
    et fournit une interface simple pour:
    - Enregistrer les nœuds
    - Sauvegarder les métriques
    - Gérer les alertes
    - Obtenir des statistiques
    """
    
    def __init__(self):
        """Initialise le gestionnaire de base de données"""
        self.logger = Journalisation()
        
        try:
            # Créer le pool de connexions
            self.pool = ConnectionPool("supervision_pool", DB_POOL_SIZE)
            self.logger.info("✅ DatabaseManager initialisé")
            
            # Vérifier la connexion et initialiser les tables si nécessaire
            self._initialiser_tables()
            
        except Exception as e:
            self.logger.error(f"❌ Erreur d'initialisation DatabaseManager: {e}")
            raise
    
    def _initialiser_tables(self):
        """Vérifie/crée les tables nécessaires"""
        try:
            # Vérifier si les tables existent
            resultats = self.pool.executer_requete("SHOW TABLES")
            tables_existantes = [list(r.values())[0] for r in resultats] if resultats else []
            
            tables_necessaires = ['noeuds', 'metriques', 'alertes']
            tables_manquantes = [t for t in tables_necessaires if t not in tables_existantes]
            
            if tables_manquantes:
                self.logger.info(f"📝 Tables manquantes: {tables_manquantes}, création...")
                self._creer_tables()
            else:
                self.logger.info("✅ Toutes les tables existent")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification tables: {e}")
    
    def _creer_tables(self):
        """Crée les tables dans la base de données"""
        # Table des nœuds
        sql_noeuds = """
        CREATE TABLE IF NOT EXISTS noeuds (
            id INT PRIMARY KEY AUTO_INCREMENT,
            node_id VARCHAR(50) UNIQUE NOT NULL,
            systeme_exploitation VARCHAR(100),
            type_processeur VARCHAR(100),
            date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            derniere_connexion TIMESTAMP NULL,
            statut ENUM('actif', 'inactif', 'panne') DEFAULT 'inactif',
            INDEX idx_node_id (node_id),
            INDEX idx_statut (statut)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        # Table des métriques
        sql_metriques = """
        CREATE TABLE IF NOT EXISTS metriques (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            node_id VARCHAR(50) NOT NULL,
            horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            charge_cpu FLOAT,
            charge_memoire FLOAT,
            stockage_disk FLOAT,
            uptime BIGINT,
            FOREIGN KEY (node_id) REFERENCES noeuds(node_id),
            INDEX idx_node_horodatage (node_id, horodatage)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        # Table des alertes
        sql_alertes = """
        CREATE TABLE IF NOT EXISTS alertes (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            node_id VARCHAR(50) NOT NULL,
            type_alerte ENUM('cpu', 'memoire', 'disque', 'panne') NOT NULL,
            valeur FLOAT,
            seuil FLOAT,
            horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (node_id) REFERENCES noeuds(node_id),
            INDEX idx_horodatage (horodatage)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        # Exécuter les créations de tables
        self.pool.executer_requete(sql_noeuds, fetch=False)
        self.pool.executer_requete(sql_metriques, fetch=False)
        self.pool.executer_requete(sql_alertes, fetch=False)
        
        self.logger.info("✅ Tables créées avec succès")
    
    # ============================================
    # OPÉRATIONS SUR LES NŒUDS
    # ============================================
    
    def enregistrer_noeud(self, node_id, infos):
        """
        Enregistre ou met à jour un nœud
        
        Args:
            node_id (str): Identifiant du nœud
            infos (dict): Informations système
        """
        sql = """
            INSERT INTO noeuds (node_id, systeme_exploitation, type_processeur, statut, derniere_connexion)
            VALUES (%s, %s, %s, 'actif', NOW())
            ON DUPLICATE KEY UPDATE
            systeme_exploitation = VALUES(systeme_exploitation),
            type_processeur = VALUES(type_processeur),
            statut = 'actif',
            derniere_connexion = NOW()
        """
        
        params = (
            node_id,
            infos.get('os', 'Inconnu'),
            infos.get('processeur', 'Inconnu')
        )
        
        self.pool.executer_requete(sql, params, fetch=False)
        self.logger.debug(f"📝 Nœud enregistré: {node_id}")
    
    def mettre_a_jour_connexion(self, node_id):
        """
        Met à jour la date de dernière connexion d'un nœud
        
        Args:
            node_id (str): Identifiant du nœud
        """
        sql = """
            UPDATE noeuds 
            SET derniere_connexion = NOW(), statut = 'actif'
            WHERE node_id = %s
        """
        
        self.pool.executer_requete(sql, (node_id,), fetch=False)
    
    def mettre_a_jour_statut_noeud(self, node_id, statut):
        """
        Met à jour le statut d'un nœud
        
        Args:
            node_id (str): Identifiant du nœud
            statut (str): Nouveau statut ('actif', 'inactif', 'panne')
        """
        sql = "UPDATE noeuds SET statut = %s WHERE node_id = %s"
        self.pool.executer_requete(sql, (statut, node_id), fetch=False)
        self.logger.info(f"📝 Statut {node_id} mis à jour: {statut}")
    
    # ============================================
    # OPÉRATIONS SUR LES MÉTRIQUES
    # ============================================
    
    def sauvegarder_metriques(self, node_id, cpu, memoire, disque, uptime):
        """
        Sauvegarde les métriques d'un nœud
        
        Args:
            node_id (str): Identifiant du nœud
            cpu (float): Charge CPU
            memoire (float): Charge mémoire
            disque (float): Utilisation disque
            uptime (int): Temps d'activité
        """
        sql = """
            INSERT INTO metriques (node_id, charge_cpu, charge_memoire, stockage_disk, uptime)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        params = (node_id, cpu, memoire, disque, uptime)
        self.pool.executer_requete(sql, params, fetch=False)
        
        # Mettre à jour la connexion
        self.mettre_a_jour_connexion(node_id)
    
    # ============================================
    # OPÉRATIONS SUR LES ALERTES
    # ============================================
    
    def enregistrer_alerte(self, node_id, type_alerte, valeur, seuil):
        """
        Enregistre une alerte
        
        Args:
            node_id (str): Identifiant du nœud
            type_alerte (str): Type d'alerte ('cpu', 'memoire', 'disque', 'panne')
            valeur (float): Valeur mesurée
            seuil (float): Seuil déclencheur
        """
        sql = """
            INSERT INTO alertes (node_id, type_alerte, valeur, seuil)
            VALUES (%s, %s, %s, %s)
        """
        
        params = (node_id, type_alerte, valeur, seuil)
        self.pool.executer_requete(sql, params, fetch=False)
        self.logger.debug(f"🚨 Alerte enregistrée: {node_id} - {type_alerte}")
    
    # ============================================
    # REQUÊTES DE LECTURE
    # ============================================
    
    def get_infos_noeud(self, node_id):
        """
        Récupère les informations détaillées d'un nœud
        
        Args:
            node_id (str): Identifiant du nœud
            
        Returns:
            str: Informations formatées
        """
        # Infos du nœud
        sql_noeud = "SELECT * FROM noeuds WHERE node_id = %s"
        resultats = self.pool.executer_requete(sql_noeud, (node_id,))
        
        if not resultats:
            return f"❌ Nœud {node_id} non trouvé"
        
        noeud = resultats[0]
        
        # Dernières métriques
        sql_metriques = """
            SELECT * FROM metriques 
            WHERE node_id = %s 
            ORDER BY horodatage DESC 
            LIMIT 5
        """
        metriques = self.pool.executer_requete(sql_metriques, (node_id,)) or []
        
        # Dernières alertes
        sql_alertes = """
            SELECT * FROM alertes 
            WHERE node_id = %s 
            ORDER BY horodatage DESC 
            LIMIT 5
        """
        alertes = self.pool.executer_requete(sql_alertes, (node_id,)) or []
        
        # Formatage
        result = []
        result.append(f"\n{'='*60}")
        result.append(f"📌 INFORMATIONS DU NŒUD: {node_id}")
        result.append(f"{'='*60}")
        result.append(f"🖥️  OS: {noeud['systeme_exploitation']}")
        result.append(f"⚙️  Processeur: {noeud['type_processeur']}")
        result.append(f"📊 Statut: {noeud['statut']}")
        result.append(f"📅 Inscrit le: {noeud['date_inscription']}")
        result.append(f"⏱ Dernière connexion: {noeud['derniere_connexion']}")
        
        if metriques:
            result.append(f"\n📈 Dernières métriques:")
            for m in metriques:
                result.append(
                    f"  {m['horodatage'].strftime('%H:%M:%S')}: "
                    f"CPU={m['charge_cpu']}%, "
                    f"MEM={m['charge_memoire']}%, "
                    f"DISK={m['stockage_disk']}%"
                )
        
        if alertes:
            result.append(f"\n🚨 Dernières alertes:")
            for a in alertes:
                result.append(
                    f"  {a['horodatage'].strftime('%H:%M:%S')}: "
                    f"{a['type_alerte']} {a['valeur']:.1f}/{a['seuil']}"
                )
        
        return '\n'.join(result)
    
    def get_dernieres_alertes(self, limite=10):
        """
        Récupère les dernières alertes
        
        Args:
            limite (int): Nombre d'alertes à récupérer
            
        Returns:
            str: Alertes formatées
        """
        sql = """
            SELECT a.*, n.systeme_exploitation 
            FROM alertes a
            JOIN noeuds n ON a.node_id = n.node_id
            ORDER BY a.horodatage DESC
            LIMIT %s
        """
        
        alertes = self.pool.executer_requete(sql, (limite,))
        
        if not alertes:
            return "📭 Aucune alerte"
        
        result = []
        for a in alertes:
            result.append(
                f"{a['horodatage'].strftime('%Y-%m-%d %H:%M:%S')} | "
                f"{a['node_id']:<10} | "
                f"{a['type_alerte']:<7} | "
                f"{a['valeur']:.1f}/{a['seuil']}"
            )
        
        return '\n'.join(result)
    
    def get_statistiques(self):
        """
        Récupère les statistiques globales
        
        Returns:
            str: Statistiques formatées
        """
        stats = []
        
        # Nombre de nœuds par statut
        sql_noeuds = "SELECT statut, COUNT(*) as count FROM noeuds GROUP BY statut"
        noeuds = self.pool.executer_requete(sql_noeuds) or []
        
        if noeuds:
            stats.append(f"\n📊 NŒUDS:")
            for n in noeuds:
                stats.append(f"  {n['statut']}: {n['count']}")
        
        # Moyennes des métriques (dernière heure)
        sql_moyennes = """
            SELECT 
                AVG(charge_cpu) as avg_cpu,
                AVG(charge_memoire) as avg_mem,
                AVG(stockage_disk) as avg_disk,
                COUNT(*) as nb_mesures
            FROM metriques
            WHERE horodatage > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """
        moyennes = self.pool.executer_requete(sql_moyennes)
        
        if moyennes and moyennes[0]['avg_cpu']:
            m = moyennes[0]
            stats.append(f"\n📈 MOYENNES (dernière heure):")
            stats.append(f"  CPU: {m['avg_cpu']:.1f}%")
            stats.append(f"  Mémoire: {m['avg_mem']:.1f}%")
            stats.append(f"  Disque: {m['avg_disk']:.1f}%")
            stats.append(f"  Mesures: {m['nb_mesures']}")
        
        # Nombre d'alertes aujourd'hui
        sql_alertes = """
            SELECT COUNT(*) as count 
            FROM alertes 
            WHERE DATE(horodatage) = CURDATE()
        """
        alertes = self.pool.executer_requete(sql_alertes)
        if alertes:
            stats.append(f"\n🚨 Alertes aujourd'hui: {alertes[0]['count']}")
        
        # Statistiques du pool
        stats.append(f"\n⚙️ POOL DE CONNEXIONS:")
        pool_stats = self.pool.get_statistiques()
        stats.append(f"  Connexions utilisées: {pool_stats['connexions_utilisees']}")
        stats.append(f"  Taux utilisation: {pool_stats['taux_utilisation']}%")
        stats.append(f"  Temps moyen attente: {pool_stats['temps_moyen_attente']}s")
        
        return '\n'.join(stats)
    
    def get_noeuds_actifs(self):
        """
        Récupère la liste des nœuds actifs
        
        Returns:
            list: Liste des nœuds actifs
        """
        sql = """
            SELECT node_id, derniere_connexion, statut 
            FROM noeuds 
            WHERE statut = 'actif'
            ORDER BY node_id
        """
        return self.pool.executer_requete(sql) or []
    
    def nettoyer_anciennes_donnees(self, jours=30):
        """
        Nettoie les données plus anciennes que 'jours'
        
        Args:
            jours (int): Âge maximum des données à conserver
        """
        sql_metriques = "DELETE FROM metriques WHERE horodatage < DATE_SUB(NOW(), INTERVAL %s DAY)"
        sql_alertes = "DELETE FROM alertes WHERE horodatage < DATE_SUB(NOW(), INTERVAL %s DAY)"
        
        self.pool.executer_requete(sql_metriques, (jours,), fetch=False)
        self.pool.executer_requete(sql_alertes, (jours,), fetch=False)
        
        self.logger.info(f"🧹 Nettoyage des données > {jours} jours effectué")
    
    def fermer(self):
        """Ferme toutes les connexions"""
        self.logger.info("🔄 Fermeture du DatabaseManager...")
        if hasattr(self, 'pool'):
            self.pool.fermer_pool()
        self.logger.info("✅ DatabaseManager fermé")


# ============================================
# EXEMPLE D'UTILISATION
# ============================================

if __name__ == "__main__":
    print("🧪 Test du DatabaseManager")
    print("="*50)
    
    # Créer le gestionnaire
    db = DatabaseManager()
    
    # Tester l'enregistrement d'un nœud
    db.enregistrer_noeud("test1", {
        'os': 'Windows 11',
        'processeur': 'Intel Core i7'
    })
    
    # Tester la sauvegarde de métriques
    db.sauvegarder_metriques("test1", 45.2, 62.5, 38.7, 3600)
    
    # Tester une alerte
    db.enregistrer_alerte("test1", "cpu", 95.0, 90.0)
    
    # Récupérer les infos
    print(db.get_infos_noeud("test1"))
    print("\n" + db.get_statistiques())
    print("\n" + db.get_dernieres_alertes())
    
    # Fermer
    db.fermer()
    print("="*50)
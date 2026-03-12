#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de pool de connexions à la base de données
Gère un pool de connexions MySQL pour optimiser les accès concurrents
"""

import mysql.connector
from mysql.connector import pooling
import threading
import time
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from commun.constantes import DB_CONFIG, DB_POOL_SIZE, DB_MAX_POOL_SIZE
from serveur.journalisation import Journalisation

class ConnectionPool:
    """
    Pool de connexions à la base de données
    
    Ce pool permet de réutiliser des connexions existantes plutôt que
    d'en créer une nouvelle à chaque requête, ce qui améliore les performances
    en environnement multi-thread.
    
    Comparaison des approches:
    - Sans pool: Chaque thread crée/supprime sa connexion (lent, gourmand)
    - Avec pool: Les threads empruntent/retournent des connexions (rapide, efficace)
    """
    
    def __init__(self, pool_name="supervision_pool", pool_size=DB_POOL_SIZE):
        """
        Initialise le pool de connexions
        
        Args:
            pool_name (str): Nom du pool
            pool_size (int): Taille initiale du pool
        """
        self.logger = Journalisation()
        self.pool_name = pool_name
        self.pool_size = pool_size
        self.pool = None
        self._initialiser_pool()
        
        # Statistiques du pool
        self.statistiques = {
            'connexions_crees': 0,
            'connexions_utilisees': 0,
            'connexions_rendues': 0,
            'connexions_fermees': 0,
            'temps_attente_total': 0,
            'nb_attentes': 0
        }
        self.lock_stats = threading.Lock()
    
    def _initialiser_pool(self):
        """Initialise le pool de connexions MySQL"""
        try:
            # Configuration du pool
            config = {
                'pool_name': self.pool_name,
                'pool_size': self.pool_size,
                'pool_reset_session': True,
                'use_pure': True,
                'autocommit': True,
                **DB_CONFIG
            }
            
            # Création du pool
            self.pool = mysql.connector.pooling.MySQLConnectionPool(**config)
            
            # Tester une connexion
            conn = self.pool.get_connection()
            conn.close()
            
            self.logger.info(f"✅ Pool de connexions initialisé: {self.pool_name} (taille: {self.pool_size})")
            
        except mysql.connector.Error as e:
            self.logger.error(f"❌ Erreur création pool MySQL: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Erreur inattendue: {e}")
            raise
    
    def get_connexion(self, timeout=30):
        """
        Obtient une connexion du pool
        
        Args:
            timeout (int): Temps maximum d'attente en secondes
            
        Returns:
            connection: Connexion MySQL ou None si timeout
        """
        debut = time.time()
        
        try:
            # Tentative d'obtention d'une connexion
            conn = self.pool.get_connection()
            
            # Mettre à jour les statistiques
            with self.lock_stats:
                self.statistiques['connexions_utilisees'] += 1
                self.statistiques['connexions_crees'] += 1
                
            return conn
            
        except pooling.PoolError as e:
            # Pool plein, attendre et réessayer
            self.logger.warning(f"⚠ Pool plein, tentative d'attente...")
            
            with self.lock_stats:
                self.statistiques['nb_attentes'] += 1
            
            # Attendre qu'une connexion se libère
            temps_attente = 0
            while temps_attente < timeout:
                time.sleep(0.5)
                temps_attente += 0.5
                
                try:
                    conn = self.pool.get_connection()
                    
                    # Enregistrer le temps d'attente
                    with self.lock_stats:
                        self.statistiques['temps_attente_total'] += temps_attente
                        self.statistiques['connexions_utilisees'] += 1
                    
                    self.logger.debug(f"✅ Connexion obtenue après {temps_attente:.1f}s d'attente")
                    return conn
                    
                except pooling.PoolError:
                    continue
            
            self.logger.error(f"❌ Timeout après {timeout}s d'attente")
            return None
            
        except mysql.connector.Error as e:
            self.logger.error(f"❌ Erreur MySQL: {e}")
            return None
    
    def liberer_connexion(self, conn):
        """
        Libère une connexion et la retourne au pool
        
        Args:
            conn: Connexion à libérer
        """
        if conn:
            try:
                conn.close()
                with self.lock_stats:
                    self.statistiques['connexions_rendues'] += 1
            except Exception as e:
                self.logger.error(f"❌ Erreur lors de la libération: {e}")
    
    def executer_requete(self, requete, params=None, fetch=True):
        """
        Exécute une requête SQL avec gestion automatique des connexions
        
        Args:
            requete (str): Requête SQL
            params (tuple/list): Paramètres de la requête
            fetch (bool): Récupérer les résultats ou non
            
        Returns:
            list/None: Résultats de la requête
        """
        conn = None
        cursor = None
        
        try:
            # Obtenir une connexion
            conn = self.get_connexion()
            if not conn:
                self.logger.error("❌ Impossible d'obtenir une connexion")
                return None
            
            # Créer un curseur
            cursor = conn.cursor(dictionary=True)
            
            # Exécuter la requête
            if params:
                cursor.execute(requete, params)
            else:
                cursor.execute(requete)
            
            # Commit pour les modifications
            conn.commit()
            
            # Récupérer les résultats si nécessaire
            if fetch:
                return cursor.fetchall()
            return None
            
        except mysql.connector.Error as e:
            self.logger.error(f"❌ Erreur SQL: {e}")
            self.logger.error(f"   Requête: {requete}")
            if params:
                self.logger.error(f"   Paramètres: {params}")
            return None
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.liberer_connexion(conn)
    
    def executer_transaction(self, requetes):
        """
        Exécute plusieurs requêtes dans une transaction
        
        Args:
            requetes (list): Liste de tuples (requete, params)
            
        Returns:
            bool: True si succès, False sinon
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connexion()
            if not conn:
                return False
            
            # Désactiver l'autocommit pour la transaction
            conn.autocommit = False
            cursor = conn.cursor()
            
            # Exécuter toutes les requêtes
            for requete, params in requetes:
                if params:
                    cursor.execute(requete, params)
                else:
                    cursor.execute(requete)
            
            # Valider la transaction
            conn.commit()
            return True
            
        except Exception as e:
            # Annuler la transaction en cas d'erreur
            if conn:
                conn.rollback()
            self.logger.error(f"❌ Erreur transaction: {e}")
            return False
            
        finally:
            if conn:
                conn.autocommit = True
            if cursor:
                cursor.close()
            if conn:
                self.liberer_connexion(conn)
    
    def get_statistiques(self):
        """
        Retourne les statistiques du pool
        
        Returns:
            dict: Statistiques d'utilisation
        """
        with self.lock_stats:
            stats = self.statistiques.copy()
            
            # Calculer quelques métriques
            if stats['connexions_crees'] > 0:
                stats['taux_utilisation'] = round(
                    stats['connexions_utilisees'] / stats['connexions_crees'] * 100, 1
                )
            else:
                stats['taux_utilisation'] = 0
                
            if stats['nb_attentes'] > 0:
                stats['temps_moyen_attente'] = round(
                    stats['temps_attente_total'] / stats['nb_attentes'], 2
                )
            else:
                stats['temps_moyen_attente'] = 0
            
            return stats
    
    def fermer_pool(self):
        """Ferme toutes les connexions du pool"""
        self.logger.info("🔄 Fermeture du pool de connexions...")
        
        # MySQL Connector/Python gère automatiquement la fermeture
        self.logger.info(f"✅ Pool fermé - Statistiques finales: {self.get_statistiques()}")


# ============================================
# EXEMPLE D'UTILISATION
# ============================================

if __name__ == "__main__":
    print("🧪 Test du pool de connexions")
    print("="*50)
    
    # Créer le pool
    pool = ConnectionPool("test_pool", 3)
    
    # Tester une requête simple
    resultats = pool.executer_requete("SELECT 1 as test")
    print(f"Test requête: {resultats}")
    
    # Afficher les statistiques
    print(f"Statistiques: {pool.get_statistiques()}")
    
    # Fermer
    pool.fermer_pool()
    print("="*50)
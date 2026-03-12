#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de journalisation des événements
"""

import logging
import os
from datetime import datetime

class Journalisation:
    """Gestionnaire de logs singleton"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialise()
        return cls._instance
    
    def _initialise(self):
        """Initialise le système de logging"""
        # Créer le dossier logs s'il n'existe pas
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Configuration du logger
        self.logger = logging.getLogger('supervision')
        self.logger.setLevel(logging.DEBUG)
        
        # Format des logs
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler pour fichier
        fichier_log = f"logs/supervision_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(fichier_log, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Handler pour console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message):
        """Log de niveau INFO"""
        self.logger.info(message)
    
    def debug(self, message):
        """Log de niveau DEBUG"""
        self.logger.debug(message)
    
    def warning(self, message):
        """Log de niveau WARNING"""
        self.logger.warning(message)
    
    def error(self, message):
        """Log de niveau ERROR"""
        self.logger.error(message)
    
    def alerte(self, message):
        """Log d'alerte (niveau WARNING)"""
        self.logger.warning(f"🚨 ALERTE: {message}")
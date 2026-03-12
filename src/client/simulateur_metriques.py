#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de simulation des métriques système
"""

import random
import time
import platform

class SimulateurMetriques:
    """Simulateur de métriques système pour les tests"""
    
    def __init__(self, node_id):
        self.node_id = node_id
        self.os = platform.system()
        self.processeur = platform.processor()
        self.start_time = time.time()
        self.random = random.Random()
        self.random.seed(hash(node_id) % 1000)  # Seed déterministe par nœud
        
    def simuler_charge_cpu(self):
        """Simule la charge CPU"""
        # Simulation réaliste avec des variations
        base = 20 + (hash(self.node_id) % 30)  # Charge de base dépend du nœud
        variation = self.random.random() * 30
        return round(base + variation, 1)  # Entre 20% et 80%
    
    def simuler_charge_memoire(self):
        """Simule la charge mémoire"""
        base = 30 + (hash(self.node_id) % 25)
        variation = self.random.random() * 25
        return round(base + variation, 1)
    
    def simuler_stockage_disk(self):
        """Simule l'utilisation du disque"""
        base = 40 + (hash(self.node_id) % 20)
        variation = self.random.random() * 20
        return round(base + variation, 1)
    
    def get_uptime(self):
        """Retourne le temps d'activité en secondes"""
        return int(time.time() - self.start_time)
    
    def simuler_statuts_services(self):
        """Simule les statuts des services"""
        services = {}
        
        # Services réseau (plus fiables)
        for service in ['HTTP', 'HTTPS', 'SSH']:
            # 95% de disponibilité
            services[service] = 'OK' if self.random.random() < 0.95 else 'DOWN'
        
        # Services application (moins fiables)
        for service in ['FIREFOX', 'CHROME', 'VSCODE']:
            # 85% de disponibilité
            services[service] = 'OK' if self.random.random() < 0.85 else 'DOWN'
        
        return services
    
    def simuler_statuts_ports(self):
        """Simule les statuts des ports"""
        ports = {}
        for port in [80, 443, 22, 3306]:
            # 98% de ports ouverts
            ports[str(port)] = 'OPEN' if self.random.random() < 0.98 else 'CLOSED'
        return ports
    
    def get_infos_systeme(self):
        """Retourne les informations système"""
        return {
            'os': self.os,
            'processeur': self.processeur,
            'hostname': platform.node(),
            'python_version': platform.python_version()
        }
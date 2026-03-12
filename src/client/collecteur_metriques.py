#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de collecte réelle des métriques système
Nécessite l'installation de psutil: pip install psutil
"""

import platform
import time
import socket

# Tentative d'import de psutil (optionnel)
try:
    import psutil
    PSUTIL_DISPONIBLE = True
except ImportError:
    PSUTIL_DISPONIBLE = False
    print("⚠ psutil non installé. Installez-le avec: pip install psutil")

class CollecteurMetriques:
    """Collecteur de métriques système réelles"""
    
    def __init__(self, node_id):
        self.node_id = node_id
        self.os = platform.system()
        self.processeur = platform.processor()
        self.start_time = time.time()
        
    def get_charge_cpu(self):
        """Retourne la charge CPU réelle"""
        if PSUTIL_DISPONIBLE:
            return round(psutil.cpu_percent(interval=1), 1)
        else:
            return 0.0
    
    def get_charge_memoire(self):
        """Retourne la charge mémoire réelle"""
        if PSUTIL_DISPONIBLE:
            mem = psutil.virtual_memory()
            return round(mem.percent, 1)
        else:
            return 0.0
    
    def get_stockage_disk(self):
        """Retourne l'utilisation du disque"""
        if PSUTIL_DISPONIBLE:
            disk = psutil.disk_usage('/')
            return round(disk.percent, 1)
        else:
            return 0.0
    
    def get_uptime(self):
        """Retourne le temps d'activité en secondes"""
        return int(time.time() - self.start_time)
    
    def get_statuts_services(self):
        """Vérifie les statuts des services"""
        services = {}
        
        if PSUTIL_DISPONIBLE:
            # Vérifier les services réseau
            services['HTTP'] = self._verifier_service_http()
            services['HTTPS'] = self._verifier_service_https()
            services['SSH'] = self._verifier_service_ssh()
            
            # Vérifier les processus des applications
            services['FIREFOX'] = self._verifier_processus('firefox')
            services['CHROME'] = self._verifier_processus('chrome')
            services['VSCODE'] = self._verifier_processus('code')
        else:
            # Mode dégradé si psutil n'est pas installé
            for service in ['HTTP', 'HTTPS', 'SSH', 'FIREFOX', 'CHROME', 'VSCODE']:
                services[service] = 'UNKNOWN'
        
        return services
    
    def _verifier_service_http(self):
        """Vérifie si le service HTTP est actif"""
        if not PSUTIL_DISPONIBLE:
            return 'UNKNOWN'
            
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and ('nginx' in proc.info['name'].lower() or 
                                         'apache' in proc.info['name'].lower() or
                                         'httpd' in proc.info['name'].lower()):
                    return 'OK'
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return 'DOWN'
    
    def _verifier_service_https(self):
        """Vérifie si le service HTTPS est actif"""
        # Même logique que HTTP généralement
        return self._verifier_service_http()
    
    def _verifier_service_ssh(self):
        """Vérifie si le service SSH est actif"""
        if not PSUTIL_DISPONIBLE:
            return 'UNKNOWN'
            
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and ('sshd' in proc.info['name'].lower() or 
                                         'ssh' in proc.info['name'].lower()):
                    return 'OK'
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return 'DOWN'
    
    def _verifier_processus(self, nom):
        """Vérifie si un processus est en cours d'exécution"""
        if not PSUTIL_DISPONIBLE:
            return 'UNKNOWN'
            
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and nom.lower() in proc.info['name'].lower():
                    return 'OK'
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return 'DOWN'
    
    def get_statuts_ports(self):
        """Vérifie les statuts des ports"""
        ports = {}
        ports_a_verifier = [80, 443, 22, 3306]
        
        for port in ports_a_verifier:
            ports[str(port)] = self._verifier_port(port)
        
        return ports
    
    def _verifier_port(self, port):
        """Vérifie si un port est ouvert"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return 'OPEN' if result == 0 else 'CLOSED'
    
    def get_infos_systeme(self):
        """Retourne les informations système"""
        infos = {
            'os': self.os,
            'processeur': self.processeur,
            'hostname': platform.node(),
            'python_version': platform.python_version()
        }
        
        if PSUTIL_DISPONIBLE:
            try:
                infos['cpu_count'] = psutil.cpu_count()
                infos['memory_total'] = psutil.virtual_memory().total // (1024**3)  # en GB
            except:
                pass
        
        return infos
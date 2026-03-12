#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
███████╗██╗   ██╗██████╗ ███████╗██████╗ ██╗   ██╗██╗███████╗██╗ ██████╗ ███╗   ██╗
██╔════╝██║   ██║██╔══██╗██╔════╝██╔══██╗██║   ██║██║██╔════╝██║██╔═══██╗████╗  ██║
███████╗██║   ██║██████╔╝█████╗  ██████╔╝██║   ██║██║███████╗██║██║   ██║██╔██╗ ██║
╚════██║██║   ██║██╔═══╝ ██╔══╝  ██╔══██╗╚██╗ ██╔╝██║╚════██║██║██║   ██║██║╚██╗██║
███████║╚██████╔╝██║     ███████╗██║  ██║ ╚████╔╝ ██║███████║██║╚██████╔╝██║ ╚████║
╚══════╝ ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝

██████╗ ███████╗███████╗███████╗ █████╗ ██╗   ██╗
██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗╚██╗ ██╔╝
██████╔╝█████╗  ███████╗█████╗  ███████║ ╚████╔╝ 
██╔══██╗██╔══╝  ╚════██║██╔══╝  ██╔══██║  ╚██╔╝  
██║  ██║███████╗███████║███████╗██║  ██║   ██║   
╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝   ╚═╝   

Système de Supervision Réseau Distribué
Version 1.0.0 - Février/Mars 2026
Projet Systèmes Répartis
"""

import sys
import os
import argparse
import subprocess
import time
import platform
from datetime import datetime
from pathlib import Path

# Couleurs pour le terminal (si supporté)
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLOR_SUPPORT = True
except ImportError:
    COLOR_SUPPORT = False
    # Créer des classes factices si colorama n'est pas installé
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = RESET = ''
    class Style:
        BRIGHT = DIM = RESET_ALL = ''

# Ajouter le chemin src au PYTHONPATH
SRC_PATH = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, SRC_PATH)

def c(text, color=None, bright=False):
    """Colorie le texte si supporté"""
    if not COLOR_SUPPORT or not color:
        return text
    
    colors = {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'blue': Fore.BLUE,
        'magenta': Fore.MAGENTA,
        'cyan': Fore.CYAN
    }
    
    style = Style.BRIGHT if bright else ''
    return f"{style}{colors.get(color, '')}{text}{Style.RESET_ALL}"

def afficher_banniere():
    """Affiche une bannière de démarrage colorée"""
    banniere = f"""
    {c('╔═══════════════════════════════════════════════════════════════════════╗', 'cyan', True)}
    {c('║', 'cyan', True)}        {c('🌟🌟🌟 SYSTÈME DE SUPERVISION RÉSEAU DISTRIBUÉ 🌟🌟🌟', 'yellow', True)}        {c('║', 'cyan', True)}
    {c('╠═══════════════════════════════════════════════════════════════════════╣', 'cyan', True)}
    {c('║', 'cyan', True)}                      {c('Version 1.0.0', 'green')}                                      {c('║', 'cyan', True)}
    {c('║', 'cyan', True)}              {c(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 'magenta')}                  {c('║', 'cyan', True)}
    {c('║', 'cyan', True)}         {c('Projet Systèmes Répartis - Février/Mars 2026', 'blue')}        {c('║', 'cyan', True)}
    {c('╚═══════════════════════════════════════════════════════════════════════╝', 'cyan', True)}
    """
    print(banniere)

def verifier_environment():
    """Vérifie l'environnement d'exécution"""
    print(f"{c('🔍 Vérification de l\'environnement...', 'cyan')}")
    
    # Vérifier Python
    python_version = platform.python_version()
    print(f"  Python: {c(python_version, 'green' if python_version >= '3.8' else 'red')}")
    
    # Vérifier les dépendances
    dependances_requises = ['mysql.connector']
    dependances_manquantes = []
    
    for dep in dependances_requises:
        try:
            __import__(dep.replace('-', '_'))
            print(f"  ✓ {dep}: {c('OK', 'green')}")
        except ImportError:
            dependances_manquantes.append(dep)
            print(f"  ✗ {dep}: {c('Manquant', 'red')}")
    
    if dependances_manquantes:
        print(f"\n{c('⚠ Certaines dépendances sont manquantes.', 'yellow')}")
        print(f"  Exécutez: {c('pip install -r requirements.txt', 'green')}")
    
    return len(dependances_manquantes) == 0

def afficher_aide():
    """Affiche l'aide détaillée"""
    aide = f"""
{c('📋 SYSTÈME DE SUPERVISION RÉSEAU - GUIDE D\'UTILISATION', 'cyan', True)}
{c('='*60, 'cyan')}

{c('COMMANDES DISPONIBLES:', 'yellow', True)}

  {c('python run.py serveur [options]', 'green')}        {c('- Lancer le serveur de supervision', 'blue')}
  {c('python run.py client <node_id> [options]', 'green')} {c('- Lancer un agent client', 'blue')}
  {c('python run.py test [options]', 'green')}           {c('- Lancer des clients de test', 'blue')}
  {c('python run.py install [options]', 'green')}        {c('- Installer la base de données', 'blue')}
  {c('python run.py status', 'green')}                   {c('- Vérifier le statut du système', 'blue')}
  {c('python run.py clean', 'green')}                    {c('- Nettoyer les logs et données', 'blue')}
  {c('python run.py help', 'green')}                     {c('- Afficher cette aide', 'blue')}

{c('📌 EXEMPLES D\'UTILISATION:', 'yellow', True)}

  {c('1. Lancer le serveur:', 'magenta')}
     {c('   python run.py serveur', 'cyan')}
     {c('   python run.py serveur --port 8888', 'cyan')}

  {c('2. Lancer des agents clients:', 'magenta')}
     {c('   python run.py client serveur1', 'cyan')}
     {c('   python run.py client serveur2 --serveur 192.168.1.100 --port 8888', 'cyan')}
     {c('   python run.py client serveur3 --mode reel', 'cyan')}

  {c('3. Tester avec plusieurs clients:', 'magenta')}
     {c('   python run.py test --clients 5', 'cyan')}
     {c('   python run.py test --clients 10 --serveur 192.168.1.100', 'cyan')}

  {c('4. Installer la base de données:', 'magenta')}
     {c('   python run.py install --db-user root', 'cyan')}
     {c('   python run.py install --db-user root --db-password monmotdepasse', 'cyan')}

{c('⚙️  OPTIONS DISPONIBLES:', 'yellow', True)}

  {c('Options serveur:', 'green')}
    --port PORT           Port d'écoute (défaut: 8888)
    --config FILE         Fichier de configuration (défaut: config/config.ini)

  {c('Options client:', 'green')}
    --serveur ADDR        Adresse du serveur (défaut: localhost)
    --port PORT           Port du serveur (défaut: 8888)
    --mode MODE           Mode: simulation ou reel (défaut: simulation)

  {c('Options test:', 'green')}
    --clients N           Nombre de clients à lancer (défaut: 3)
    --serveur ADDR        Adresse du serveur (défaut: localhost)
    --port PORT           Port du serveur (défaut: 8888)

  {c('Options install:', 'green')}
    --db-user USER        Utilisateur MySQL (défaut: root)
    --db-password PASS    Mot de passe MySQL

{c('📁 STRUCTURE DU PROJET:', 'yellow', True)}
  {c('SupervisionReseau/', 'cyan')}
  {c('├── src/              # Code source', 'cyan')}
  {c('├── scripts/          # Scripts SQL', 'cyan')}
  {c('├── config/           # Fichiers de configuration', 'cyan')}
  {c('├── logs/             # Fichiers de log', 'cyan')}
  {c('├── requirements.txt  # Dépendances', 'cyan')}
  {c('└── run.py            # Point d\'entrée', 'cyan')}

{c('💡 CONSEILS:', 'yellow', True)}
  {c('• Commencez toujours par lancer le serveur avant les clients', 'blue')}
  {c('• Utilisez --mode reel pour collecter de vraies métriques (nécessite psutil)', 'blue')}
  {c('• Les logs sont dans le dossier logs/ pour le débogage', 'blue')}
  {c('• Pour arrêter: Ctrl+C', 'blue')}
"""
    print(aide)

def mode_serveur(args):
    """Mode serveur"""
    print(f"{c('🚀', 'green', True)} {c('Démarrage du serveur de supervision...', 'green', True)}")
    print(f"  {c('📡 Port:', 'cyan')} {c(args.port, 'yellow')}")
    print(f"  {c('📄 Configuration:', 'cyan')} {c(args.config, 'yellow')}")
    
    try:
        from src.serveur.serveur_supervision import main as serveur_main
        # Rediriger les arguments
        sys.argv = [sys.argv[0], str(args.port)]
        serveur_main()
    except ImportError as e:
        print(f"{c('❌ Erreur:', 'red', True)} Impossible de charger le module serveur")
        print(f"  {c('Détail:', 'red')} {e}")
        print(f"  Vérifiez que le dossier src/serveur existe avec les fichiers nécessaires")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{c('👋 Serveur arrêté', 'yellow')}")
    except Exception as e:
        print(f"{c('❌ Erreur:', 'red', True)} {e}")
        sys.exit(1)

def mode_client(args):
    """Mode client"""
    print(f"{c('📱', 'blue', True)} {c(f'Démarrage de l\'agent {args.node_id}...', 'blue', True)}")
    print(f"  {c('📡 Serveur:', 'cyan')} {c(f'{args.serveur}:{args.port}', 'yellow')}")
    print(f"  {c('⚙️  Mode:', 'cyan')} {c(args.mode, 'yellow')}")
    
    try:
        from src.client.agent_supervision import main as client_main
        # Rediriger les arguments
        sys.argv = [sys.argv[0], args.node_id, args.serveur, args.mode]
        client_main()
    except ImportError as e:
        print(f"{c('❌ Erreur:', 'red', True)} Impossible de charger le module client")
        print(f"  {c('Détail:', 'red')} {e}")
        print(f"  Vérifiez que le dossier src/client existe avec les fichiers nécessaires")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{c('👋 Agent arrêté', 'yellow')}")
    except Exception as e:
        print(f"{c('❌ Erreur:', 'red', True)} {e}")
        sys.exit(1)

def mode_test(args):
    """Mode test - lance plusieurs clients"""
    print(f"{c('🧪', 'magenta', True)} {c(f'Lancement de {args.clients} clients de test...', 'magenta', True)}")
    print(f"  {c('📡 Serveur cible:', 'cyan')} {c(f'{args.serveur}:{args.port}', 'yellow')}")
    
    processus = []
    
    try:
        for i in range(1, args.clients + 1):
            node_id = f"test{i}"
            print(f"  {c('▶', 'green')} Lancement de {c(node_id, 'yellow')}...")
            
            # Commande à exécuter
            cmd = [
                sys.executable, "run.py", "client", node_id,
                "--serveur", args.serveur,
                "--port", str(args.port),
                "--mode", "simulation"
            ]
            
            # Lancer le processus
            if platform.system() == "Windows":
                proc = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            processus.append(proc)
            time.sleep(0.3)  # Petit délai entre chaque lancement
        
        print(f"\n{c('✅', 'green', True)} {c(f'{args.clients} clients lancés avec succès', 'green')}")
        print(f"{c('⌨️  Appuyez sur Entrée pour arrêter tous les clients...', 'cyan')}")
        input()
        
    except KeyboardInterrupt:
        print(f"\n{c('🛑 Arrêt demandé...', 'yellow')}")
    finally:
        # Arrêter tous les processus
        print(f"{c('🔄 Arrêt des clients...', 'cyan')}")
        for proc in processus:
            try:
                proc.terminate()
            except:
                pass
        print(f"{c('👋 Tous les clients arrêtés', 'green')}")

def mode_install(args):
    """Mode installation de la base de données"""
    print(f"{c('🗄️', 'yellow', True)} {c('Installation de la base de données...', 'yellow', True)}")
    
    # Vérifier que le script SQL existe
    sql_path = Path('scripts/create_db.sql')
    if not sql_path.exists():
        print(f"{c('❌ Erreur:', 'red')} Fichier {c('scripts/create_db.sql', 'yellow')} non trouvé")
        return
    
    # Construire la commande MySQL
    cmd = ["mysql", "-u", args.db_user]
    if args.db_password:
        cmd.extend([f"-p{args.db_password}"])
    else:
        cmd.append("-p")  # Demandera le mot de passe interactivement
    
    try:
        # Lire le fichier SQL
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"{c('📦 Exécution du script SQL...', 'cyan')}")
        
        # Exécuter la commande
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=sql_content)
        
        if process.returncode == 0:
            print(f"{c('✅', 'green', True)} {c('Base de données installée avec succès', 'green')}")
            if stdout:
                print(f"\n{stdout}")
        else:
            print(f"{c('❌ Erreur MySQL:', 'red')}\n{stderr}")
            
    except FileNotFoundError:
        print(f"{c('❌ Erreur:', 'red')} MySQL non trouvé dans le PATH")
        print(f"  Vérifiez que MySQL est installé: {c('https://dev.mysql.com/downloads/', 'blue')}")
    except Exception as e:
        print(f"{c('❌ Erreur:', 'red')} {e}")

def mode_status(args):
    """Vérifie le statut du système"""
    print(f"{c('📊', 'blue', True)} {c('Statut du système', 'blue', True)}")
    print(f"{c('='*50, 'blue')}")
    
    # Vérifier l'environnement
    verifier_environment()
    
    # Vérifier la base de données
    print(f"\n{c('🗄️  Base de données:', 'cyan')}")
    try:
        from src.database.database_manager import DatabaseManager
        db = DatabaseManager()
        stats = db.get_statistiques()
        print(f"  {c('✓ Connexion OK', 'green')}")
        db.fermer()
    except Exception as e:
        print(f"  {c('✗ Connexion impossible:', 'red')} {e}")
    
    # Afficher les logs récents
    log_path = Path('logs/supervision.log')
    if log_path.exists():
        print(f"\n{c('📝 Dernières lignes du log:', 'cyan')}")
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lignes = f.readlines()[-5:]  # Dernières 5 lignes
                for ligne in lignes:
                    print(f"  {ligne.strip()}")
        except:
            print(f"  Impossible de lire le fichier de log")

def mode_clean(args):
    """Nettoie les logs et données temporaires"""
    print(f"{c('🧹', 'yellow', True)} {c('Nettoyage du système...', 'yellow', True)}")
    
    # Nettoyer les logs
    log_dir = Path('logs')
    if log_dir.exists():
        print(f"{c('📁 Nettoyage des logs...', 'cyan')}")
        count = 0
        for log_file in log_dir.glob('*.log*'):
            try:
                log_file.unlink()
                print(f"  {c('✓ Supprimé:', 'green')} {log_file.name}")
                count += 1
            except Exception as e:
                print(f"  {c('✗ Erreur:', 'red')} {log_file.name} - {e}")
        print(f"  {c(f'{count} fichiers supprimés', 'yellow')}")
    
    # Nettoyer les caches Python
    print(f"\n{c('🐍 Nettoyage des caches Python...', 'cyan')}")
    pycache_count = 0
    for pycache in Path('src').rglob('__pycache__'):
        try:
            for file in pycache.glob('*'):
                file.unlink()
            pycache.rmdir()
            print(f"  {c('✓ Supprimé:', 'green')} {pycache}")
            pycache_count += 1
        except Exception as e:
            print(f"  {c('✗ Erreur:', 'red')} {pycache} - {e}")
    
    print(f"\n{c('✅ Nettoyage terminé', 'green', True)}")

def main():
    """Point d'entrée principal"""
    # Créer le parser principal
    parser = argparse.ArgumentParser(
        description='Système de Supervision Réseau Distribué',
        usage='python run.py <mode> [options]',
        add_help=False  # On gère l'aide manuellement
    )
    
    parser.add_argument('mode', nargs='?', help='Mode d\'exécution')
    
    # Parser pour les sous-commandes
    subparsers = parser.add_subparsers(dest='command', help='Commandes')
    
    # Serveur
    parser_serveur = subparsers.add_parser('serveur', help='Lancer le serveur')
    parser_serveur.add_argument('--port', type=int, default=8888, help='Port d\'écoute (défaut: 8888)')
    parser_serveur.add_argument('--config', type=str, default='config/config.ini', help='Fichier de configuration')
    
    # Client
    parser_client = subparsers.add_parser('client', help='Lancer un agent client')
    parser_client.add_argument('node_id', help='Identifiant du nœud')
    parser_client.add_argument('--serveur', type=str, default='localhost', help='Adresse du serveur (défaut: localhost)')
    parser_client.add_argument('--port', type=int, default=8888, help='Port du serveur (défaut: 8888)')
    parser_client.add_argument('--mode', type=str, choices=['simulation', 'reel'], default='simulation', help='Mode de collecte')
    
    # Test
    parser_test = subparsers.add_parser('test', help='Lancer des clients de test')
    parser_test.add_argument('--clients', type=int, default=3, help='Nombre de clients (défaut: 3)')
    parser_test.add_argument('--serveur', type=str, default='localhost', help='Adresse du serveur')
    parser_test.add_argument('--port', type=int, default=8888, help='Port du serveur')
    
    # Install
    parser_install = subparsers.add_parser('install', help='Installer la base de données')
    parser_install.add_argument('--db-user', type=str, default='root', help='Utilisateur MySQL')
    parser_install.add_argument('--db-password', type=str, help='Mot de passe MySQL')
    
    # Status
    parser_status = subparsers.add_parser('status', help='Vérifier le statut du système')
    
    # Clean
    parser_clean = subparsers.add_parser('clean', help='Nettoyer les logs et caches')
    
    # Help
    parser_help = subparsers.add_parser('help', help='Afficher l\'aide')
    
    # Analyser les arguments
    if len(sys.argv) == 1:
        # Pas d'arguments
        afficher_banniere()
        afficher_aide()
        return
    
    # Pour compatibilité avec l'ancienne syntaxe
    if sys.argv[1] in ['serveur', 'client', 'test', 'install', 'status', 'clean', 'help']:
        # Utiliser le nouveau système
        args = parser.parse_args()
    else:
        # Ancienne syntaxe (run.py serveur 8888)
        mode = sys.argv[1]
        if mode == 'serveur':
            port = sys.argv[2] if len(sys.argv) > 2 else '8888'
            sys.argv = [sys.argv[0], 'serveur', '--port', port]
        elif mode == 'client':
            node_id = sys.argv[2] if len(sys.argv) > 2 else 'test1'
            serveur = sys.argv[3] if len(sys.argv) > 3 else 'localhost'
            mode_client = sys.argv[4] if len(sys.argv) > 4 else 'simulation'
            sys.argv = [sys.argv[0], 'client', node_id, '--serveur', serveur, '--mode', mode_client]
        args = parser.parse_args()
    
    # Afficher la bannière
    afficher_banniere()
    
    # Exécuter la commande
    if args.command == 'serveur':
        mode_serveur(args)
    elif args.command == 'client':
        mode_client(args)
    elif args.command == 'test':
        mode_test(args)
    elif args.command == 'install':
        mode_install(args)
    elif args.command == 'status':
        mode_status(args)
    elif args.command == 'clean':
        mode_clean(args)
    else:
        afficher_aide()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{c('👋 Au revoir!', 'yellow', True)}")
    except Exception as e:
        print(f"\n{c('❌ Erreur inattendue:', 'red', True)} {e}")
        import traceback
        traceback.print_exc()
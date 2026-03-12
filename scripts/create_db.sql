-- ============================================
-- SCRIPT DE CRÉATION DE LA BASE DE DONNÉES
-- Système de Supervision Réseau
-- ============================================

-- Supprimer la base si elle existe (attention en production!)
-- DROP DATABASE IF EXISTS supervision_reseau;

-- Créer la base de données
CREATE DATABASE IF NOT EXISTS supervision_reseau
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE supervision_reseau;

-- ============================================
-- TABLE DES NŒUDS
-- ============================================
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

-- ============================================
-- TABLE DES MÉTRIQUES
-- ============================================
CREATE TABLE IF NOT EXISTS metriques (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    node_id VARCHAR(50) NOT NULL,
    horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    charge_cpu FLOAT,
    charge_memoire FLOAT,
    stockage_disk FLOAT,
    uptime BIGINT,
    FOREIGN KEY (node_id) REFERENCES noeuds(node_id) ON DELETE CASCADE,
    INDEX idx_node_horodatage (node_id, horodatage)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TABLE DES SERVICES
-- ============================================
CREATE TABLE IF NOT EXISTS services (
    id INT PRIMARY KEY AUTO_INCREMENT,
    node_id VARCHAR(50) NOT NULL,
    nom_service VARCHAR(50) NOT NULL,
    statut ENUM('OK', 'DOWN', 'UNKNOWN') DEFAULT 'UNKNOWN',
    horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES noeuds(node_id) ON DELETE CASCADE,
    INDEX idx_service (node_id, nom_service)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TABLE DES PORTS
-- ============================================
CREATE TABLE IF NOT EXISTS ports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    node_id VARCHAR(50) NOT NULL,
    port INT NOT NULL,
    statut ENUM('OPEN', 'CLOSED', 'UNKNOWN') DEFAULT 'UNKNOWN',
    horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES noeuds(node_id) ON DELETE CASCADE,
    INDEX idx_port (node_id, port)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TABLE DES ALERTES
-- ============================================
CREATE TABLE IF NOT EXISTS alertes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    node_id VARCHAR(50) NOT NULL,
    type_alerte ENUM('cpu', 'memoire', 'disque', 'panne', 'service', 'port') NOT NULL,
    valeur FLOAT,
    seuil FLOAT,
    message TEXT,
    horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES noeuds(node_id) ON DELETE CASCADE,
    INDEX idx_horodatage (horodatage)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- CRÉATION DE L'UTILISATEUR
-- ============================================
CREATE USER IF NOT EXISTS 'supervision_app'@'localhost' IDENTIFIED BY 'supervision123';
GRANT ALL PRIVILEGES ON supervision_reseau.* TO 'supervision_app'@'localhost';
GRANT CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, SELECT ON supervision_reseau.* TO 'supervision_app'@'localhost';
FLUSH PRIVILEGES;

-- ============================================
-- DONNÉES DE TEST
-- ============================================

-- Insérer quelques nœuds de test
INSERT IGNORE INTO noeuds (node_id, systeme_exploitation, type_processeur, statut) VALUES
('serveur1', 'Ubuntu 22.04 LTS', 'Intel Xeon E5-2670', 'actif'),
('serveur2', 'Windows Server 2022', 'AMD EPYC 7282', 'actif'),
('serveur3', 'Debian 12 Bookworm', 'Intel Core i7-10700', 'actif'),
('serveur4', 'CentOS 9 Stream', 'AMD Ryzen 9 5950X', 'inactif'),
('serveur5', 'Red Hat 9', 'Intel Xeon Gold 6248', 'panne');

-- Insérer des métriques de test pour les dernières 24h
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS insert_test_data()
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE node VARCHAR(20);
    DECLARE cpu FLOAT;
    DECLARE mem FLOAT;
    DECLARE disk FLOAT;
    
    WHILE i < 48 DO
        -- Métriques pour serveur1
        SET cpu = 30 + RAND() * 40;
        SET mem = 40 + RAND() * 30;
        SET disk = 35 + RAND() * 20;
        INSERT INTO metriques (node_id, charge_cpu, charge_memoire, stockage_disk, uptime, horodatage) 
        VALUES ('serveur1', cpu, mem, disk, 86400 + i*1800, DATE_SUB(NOW(), INTERVAL i*30 MINUTE));
        
        -- Métriques pour serveur2 (plus chargé)
        SET cpu = 50 + RAND() * 40;
        SET mem = 60 + RAND() * 30;
        SET disk = 45 + RAND() * 25;
        INSERT INTO metriques (node_id, charge_cpu, charge_memoire, stockage_disk, uptime, horodatage) 
        VALUES ('serveur2', cpu, mem, disk, 43200 + i*1800, DATE_SUB(NOW(), INTERVAL i*30 MINUTE));
        
        -- Métriques pour serveur3
        SET cpu = 20 + RAND() * 30;
        SET mem = 30 + RAND() * 30;
        SET disk = 25 + RAND() * 20;
        INSERT INTO metriques (node_id, charge_cpu, charge_memoire, stockage_disk, uptime, horodatage) 
        VALUES ('serveur3', cpu, mem, disk, 129600 + i*1800, DATE_SUB(NOW(), INTERVAL i*30 MINUTE));
        
        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;

CALL insert_test_data();
DROP PROCEDURE IF EXISTS insert_test_data;

-- Insérer des alertes de test
INSERT IGNORE INTO alertes (node_id, type_alerte, valeur, seuil, message) VALUES
('serveur2', 'cpu', 95.2, 90.0, 'Dépassement seuil CPU'),
('serveur2', 'memoire', 92.5, 90.0, 'Dépassement seuil mémoire'),
('serveur3', 'disque', 88.3, 85.0, 'Espace disque faible'),
('serveur5', 'panne', 120, 90, 'Nœud inactif depuis 120 secondes');

-- ============================================
-- VUES UTILES
-- ============================================

-- Vue des nœuds avec leurs dernières métriques
CREATE OR REPLACE VIEW v_dernieres_metriques AS
SELECT 
    n.node_id,
    n.statut,
    n.systeme_exploitation,
    m.charge_cpu,
    m.charge_memoire,
    m.stockage_disk,
    m.horodatage as derniere_mise_a_jour
FROM noeuds n
LEFT JOIN metriques m ON m.id = (
    SELECT id FROM metriques 
    WHERE node_id = n.node_id 
    ORDER BY horodatage DESC 
    LIMIT 1
);

-- Vue des alertes récentes
CREATE OR REPLACE VIEW v_alertes_recentes AS
SELECT 
    a.*,
    n.systeme_exploitation
FROM alertes a
JOIN noeuds n ON a.node_id = n.node_id
WHERE a.horodatage > DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY a.horodatage DESC;

-- ============================================
-- STATISTIQUES
-- ============================================
SELECT '✅ Base de données créée avec succès' as Message;

SELECT 
    CONCAT('📊 Tables créées: ', COUNT(*)) as Resultat 
FROM information_schema.tables 
WHERE table_schema = 'supervision_reseau';

SELECT 
    CONCAT('📝 Nœuds insérés: ', COUNT(*)) as Resultat
FROM noeuds;

SELECT 
    CONCAT('📈 Métriques insérées: ', COUNT(*)) as Resultat
FROM metriques;
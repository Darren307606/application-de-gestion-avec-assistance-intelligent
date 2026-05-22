-- Active: 1772988907358@@127.0.0.1@3306@gestion_depenses
CREATE DATABASE gestion_depenses DEFAULT CHARACTER SET = 'utf8mb4';
USE gestion_depenses;

CREATE TABLE utilisateur (
    id_utilisateur INT AUTO_INCREMENT,
    nom_complet VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(255) NOT NULL,
    date_inscription DATE NOT NULL,
    score_sante_financiere INT DEFAULT 100,
    revenu_mensuel_moyen INT DEFAULT 0,
    CONSTRAINT pk_utilisateur PRIMARY KEY (id_utilisateur),
    CONSTRAINT chk_score_sante CHECK (score_sante_financiere BETWEEN 0 AND 100)
);

CREATE TABLE categorie (
    id_categorie INT AUTO_INCREMENT,
    nom_categorie VARCHAR(50) NOT NULL,
    icone_ou_couleur VARCHAR(50),
    type_categorie VARCHAR(50),
    CONSTRAINT pk_categorie PRIMARY KEY (id_categorie)
);

CREATE TABLE compte (
    id_compte INT AUTO_INCREMENT,
    nom_compte VARCHAR(50) NOT NULL,
    type_compte VARCHAR(50),
    solde_actuel INT DEFAULT 0,
    id_utilisateur INT NOT NULL,
    CONSTRAINT pk_compte PRIMARY KEY (id_compte),
    CONSTRAINT fk_compte_utilisateur FOREIGN KEY (id_utilisateur) 
        REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE
);

CREATE TABLE budjet_mensuel (
    id_budjet_mensuel INT AUTO_INCREMENT,
    annee INT NOT NULL,
    mois INT NOT NULL,
    montant_alloue INT NOT NULL DEFAULT 0,
    montant_depense INT DEFAULT 0,
    id_categorie INT NOT NULL,
    id_utilisateur INT NOT NULL,
    CONSTRAINT pk_budjet_mensuel PRIMARY KEY (id_budjet_mensuel),
    CONSTRAINT fk_budjet_categorie FOREIGN KEY (id_categorie) 
        REFERENCES categorie(id_categorie) ON DELETE CASCADE,
    CONSTRAINT fk_budget_utilisateur FOREIGN KEY (id_utilisateur) 
        REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE,
    CONSTRAINT chk_mois CHECK (mois BETWEEN 1 AND 12)
);

CREATE TABLE transaction (
    id_transaction INT AUTO_INCREMENT,
    montant INT NOT NULL,
    date_transaction DATE NOT NULL,
    description VARCHAR(255),
    type_transaction ENUM('DEPENSE', 'REVENU', 'TRANSFERT') NOT NULL,
    periodicite ENUM('UNIQUE', 'HEBDOMADAIRE', 'MENSUEL', 'ANNUEL') DEFAULT 'UNIQUE',
    id_compte INT NOT NULL,
    id_categorie INT NOT NULL,
    CONSTRAINT pk_transaction PRIMARY KEY (id_transaction),
    CONSTRAINT fk_transaction_compte FOREIGN KEY (id_compte) 
        REFERENCES compte(id_compte) ON DELETE CASCADE,
    CONSTRAINT fk_transaction_categorie FOREIGN KEY (id_categorie) 
        REFERENCES categorie(id_categorie) ON DELETE CASCADE
);

CREATE TABLE objectif_financier (
    id_objectif_financier INT AUTO_INCREMENT,
    titre_projet VARCHAR(100) NOT NULL,
    montant_cible INT NOT NULL,
    montant_actuel_epargne INT DEFAULT 0,
    date_cible_souhaitee DATE,
    date_estimee_reussite DATE,
    statut VARCHAR(30) DEFAULT 'En cours',
    id_utilisateur INT NOT NULL,
    CONSTRAINT pk_objectif_financier PRIMARY KEY (id_objectif_financier),
    CONSTRAINT fk_objectif_utilisateur FOREIGN KEY (id_utilisateur) 
        REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE
);

CREATE TABLE scenario_simulation (
    id_scenario_simulation INT AUTO_INCREMENT,
    nom_scenario VARCHAR(100) NOT NULL,
    nouvelle_depense_mensuelle INT DEFAULT 0,
    nouveau_montant_epargne INT DEFAULT 0,
    date_simulation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    variation_revenu DECIMAL(5,2) DEFAULT 0.00,
    id_utilisateur INT NOT NULL,
    CONSTRAINT pk_scenario PRIMARY KEY (id_scenario_simulation),
    CONSTRAINT fk_scenario_utilisateur FOREIGN KEY (id_utilisateur) 
        REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE
);

CREATE TABLE conseil_assistant (
    id_conseil_assistant INT AUTO_INCREMENT,
    type_conseil VARCHAR(50),
    message_genere TEXT NOT NULL,
    date_generation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut_lu BOOLEAN DEFAULT FALSE,
    id_utilisateur INT NOT NULL,
    CONSTRAINT pk_conseil PRIMARY KEY (id_conseil_assistant),
    CONSTRAINT fk_conseil_utilisateur FOREIGN KEY (id_utilisateur) 
        REFERENCES utilisateur(id_utilisateur) ON DELETE CASCADE
);
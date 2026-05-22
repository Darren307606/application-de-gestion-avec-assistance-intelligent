import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuration de la page Streamlit
st.set_page_config(page_title="SmartBudget Pro - YNAB + AI", layout="wide")

#  CONNEXION À LA BASE DE DONNÉES 
def obtenir_connexion_mysql():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",                 # Utilisateur par défaut sur WampServer
            password="",                 # Mot de passe par défaut (vide) sur WampServer
            database="gestion_depenses", # Nom de la base de données existante
            charset="utf8mb4"
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Erreur de connexion à WampServer (MySQL) : {err}")
        return None

# LOGIQUE MÉTIER ET FONCTIONNALITÉS DE CALCULS FINANCIERS

def extraire_metriques():
    conn = obtenir_connexion_mysql()
    if not conn:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        
    cursor = conn.cursor()
    
    # Solde global
    cursor.execute("SELECT SUM(solde_actuel) FROM compte")
    res_solde = cursor.fetchone()
    solde_total = res_solde[0] if res_solde and res_solde[0] is not None else 0.0
    
    # Revenu moyen configuré (Correction du bug de l'objet NoneType)
    cursor.execute("SELECT revenu_mensuel_moyen FROM utilisateur WHERE id_utilisateur = 1")
    res_revenu = cursor.fetchone()
    revenu_moyen = res_revenu[0] if res_revenu and res_revenu[0] is not None else 0.0
    
    # Budgets du mois en cours
    now = datetime.now()
    cursor.execute("SELECT SUM(montant_alloue) FROM budjet_mensuel WHERE mois = %s AND annee = %s", (now.month, now.year))
    res_alloue = cursor.fetchone()
    total_alloue = res_alloue[0] if res_alloue and res_alloue[0] is not None else 0.0
    
    cursor.execute("SELECT SUM(montant_depense) FROM budjet_mensuel WHERE mois = %s AND annee = %s", (now.month, now.year))
    res_depense = cursor.fetchone()
    total_depense = res_depense[0] if res_depense and res_depense[0] is not None else 0.0
    
    # Calcul des économies / épargne stockée
    cursor.execute("SELECT SUM(montant_actuel_epargne) FROM objectif_financier")
    res_epargne = cursor.fetchone()
    total_epargne = res_epargne[0] if res_epargne and res_epargne[0] is not None else 0.0
    
    # Taux d'épargne théorique basé sur le revenu configuré
    taux_epargne = round((total_epargne / revenu_moyen * 100), 1) if revenu_moyen > 0 else 0.0
    
    # Calcul du Reste Disponible (Formule YNAB : Revenu - Montants alloués aux enveloppes)
    reste_disponible = revenu_moyen - total_alloue
    
    cursor.close()
    conn.close()
    return solde_total, revenu_moyen, total_alloue, total_depense, total_epargne, reste_disponible, taux_epargne

# Évaluation dynamique du Bonus : Indice de Santé Financière (0 à 100)
def calculer_indice_sante(revenu, total_depense, total_alloue):
    if revenu == 0:
        return 100
    score = 100
    
    conn = obtenir_connexion_mysql()
    if not conn:
        return 100
        
    now = datetime.now()
    df_b = pd.read_sql_query(
        "SELECT montant_alloue, montant_depense FROM budjet_mensuel WHERE mois = %s AND annee = %s", 
        conn, params=(now.month, now.year)
    )
    conn.close()
    
    if not df_b.empty:
        depassements = df_b[df_b['montant_depense'] > df_b['montant_alloue']]
        score -= (len(depassements) * 15) # -15 points par enveloppe brisée
        
    # Facteur 2 : Niveau de dépenses global par rapport au revenu
    if total_depense > revenu:
        score -= 40
    elif total_depense > (revenu * 0.85):
        score -= 20
        
    return max(0, min(100, score))

# INTERFACE  STREAMLIT CONTENANT TOUTES LES FONCTIONNALITÉS
st.title("SmartBudget Pro")
st.subheader("Modèle YNAB augmenté par Intelligence Artificielle et Simulateur Temporel")

# Navigation principale latérale
menu = st.sidebar.radio("Sélectionner un module de l'application", [
    "Paramétrage Initial",
    "Tableau de Bord & Indice de Santé",
    "Enveloppes Budgétaires (YNAB)",
    "Saisie & Classification des Flux",
    "Assistant Financier Intelligent",
    "Simulateur de Vie Financière Future",
    "Objectifs Financiers & Épargne"
])

solde_total, revenu_moyen, total_alloue, total_depense, total_epargne, reste_disponible, taux_epargne = extraire_metriques()

# Vérification rapide de la connexion dans la barre latérale
conn_test = obtenir_connexion_mysql()
if conn_test:
    st.sidebar.success("Connecté à MySQL (WampServer)")
    conn_test.close()

#  CONFIGURATION INITIALE
if menu == "Paramétrage Initial":
    st.header("Initialisation des composants de votre infrastructure financière")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.subheader("1. Définir le Revenu de Base")
        with st.form("form_rev"):
            nouveau_rev = st.number_input("Revenu mensuel moyen (FCFA)", min_value=0, step=10000, value=int(revenu_moyen))
            if st.form_submit_button("Sauvegarder le revenu"):
                conn = obtenir_connexion_mysql()
                if conn:
                    cursor = conn.cursor()
                    # On vérifie si l'utilisateur 1 existe déjà
                    cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE id_utilisateur = 1")
                    if cursor.fetchone():
                        cursor.execute("UPDATE utilisateur SET revenu_mensuel_moyen = %s WHERE id_utilisateur = 1", (nouveau_rev,))
                    else:
                        cursor.execute("INSERT INTO utilisateur (id_utilisateur, revenu_mensuel_moyen, score_sante_financiere) VALUES (1, %s, 100)", (nouveau_rev,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success("Revenu configuré !")
                    st.rerun()
                
    with c2:
        st.subheader("2. Créer un Compte Financier")
        with st.form("form_compte"):
            n_compte = st.text_input("Nom du compte (ex: Wave, MTN, Cash, EcoBank)")
            t_compte = st.selectbox("Type", ["Banque", "Portefeuille Électronique", "Espèces", "Épargne"])
            s_compte = st.number_input("Solde initial (FCFA)", min_value=0, step=5000)
            if st.form_submit_button("Ajouter le compte"):
                if n_compte:
                    conn = obtenir_connexion_mysql()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO compte (nom_compte, type_compte, solde_actuel, id_utilisateur) VALUES (%s, %s, %s, 1)", (n_compte, t_compte, s_compte))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success("Compte ajouté !")
                        st.rerun()
                    
    with c3:
        st.subheader("3. Créer une Catégorie")
        with st.form("form_cat"):
            n_cat = st.text_input("Nom de la catégorie (ex: Nourriture, Transport)")
            t_cat = st.selectbox("Type de charge", ["Variable", "Fixe", "Épargne"])
            if st.form_submit_button("Créer la catégorie"):
                if n_cat:
                    conn = obtenir_connexion_mysql()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO categorie (nom_categorie, type_categorie) VALUES (%s, %s)", (n_cat, t_cat))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success("Catégorie enregistrée !")
                        st.rerun()

#  TABLEAU DE BORD, CALCULS FINANCIERS ET INDICE DE SANTE FINANCIERE
elif menu == "Tableau de Bord & Indice de Santé":
    st.header("Tableau de Bord & Indicateurs Financiers Actuels")
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(label="Solde cumulé des comptes", value=f"{solde_total:,.0f} FCFA")
    with k2:
        st.metric(label="Reste disponible (Formule YNAB)", value=f"{reste_disponible:,.0f} FCFA", help="Revenu - Montant alloué aux enveloppes")
    with k3:
        st.metric(label="Total dépensé ce mois", value=f"{total_depense:,.0f} FCFA")
    with k4:
        st.metric(label="Taux d'épargne calculé", value=f"{taux_epargne} %")
        
    st.markdown("---")
    
    st.subheader("Indice Fondamental de Santé Financière")
    score = calculer_indice_sante(revenu_moyen, total_depense, total_alloue)
    
    col_j, col_t = st.columns([1, 2])
    with col_j:
        fig_j = go.Figure(go.Indicator(
            mode = "gauge+number", value = score, domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [0, 100]},
                'steps': [{'range': [0, 50], 'color': '#ff4d4d'}, {'range': [50, 75], 'color': '#ffa64d'}, {'range': [75, 100], 'color': '#2eb85c'}]
            }
        ))
        fig_j.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_j, use_container_width=True)
        
    with col_t:
        if score >= 75: st.success(f"Score : {score}/100 — Situation financière stable. Félicitations, vos indicateurs sont au vert.")
        elif score >= 50: st.warning(f"Score : {score}/100 — Attention. Des tensions budgétaires ou des enveloppes dépassées sont détectées.")
        else: st.error(f"Score : {score}/100 — Risque élevé de dépassement budgétaire. Agissez immédiatement pour réduire vos charges variables.")

    st.markdown("---")
    st.subheader("Graphiques d'Analyse et de Comparaison")
    
    conn = obtenir_connexion_mysql()
    if conn:
        now = datetime.now()
        df_chart = pd.read_sql_query("""
            SELECT c.nom_categorie as Categorie, b.montant_depense as Depense, b.montant_alloue as Alloue
            FROM budjet_mensuel b JOIN categorie c ON b.id_categorie = c.id_categorie WHERE b.mois = %s AND b.annee = %s
        """, conn, params=(now.month, now.year))
        conn.close()
        
        if df_chart.empty:
            st.info("Aucun graphique disponible. Ajoutez d'abord des enveloppes budgétaires et effectuez des transactions.")
        else:
            g1, g2 = st.columns(2)
            with g1:
                st.write("Graphique circulaire : Dépenses par catégorie")
                st.plotly_chart(px.pie(df_chart, values='Depense', names='Categorie', hole=0.3), use_container_width=True)
            with g2:
                st.write("Graphique d'évolution : Alloué vs Réalité")
                st.plotly_chart(px.bar(df_chart, x='Categorie', y=['Alloue', 'Depense'], barmode='group'), use_container_width=True)

#  METHODE YNAB (ENVELOPPES BUDGETAIRES)
elif menu == "Enveloppes Budgétaires (YNAB)":
    st.header("Gestion budgétaire avancée : \"Every Dollar Has a Job\"")
    st.write("Attribuez un montant cible à chaque enveloppe budgétaire pour le mois courant.")
    
    conn = obtenir_connexion_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_categorie, nom_categorie FROM categorie")
        categories = cursor.fetchall()
        now = datetime.now()
        
        df_enveloppes = pd.read_sql_query("""
            SELECT b.id_budjet_mensuel as ID, c.nom_categorie as Categorie, b.montant_alloue as Alloue, b.montant_depense as Depense
            FROM budjet_mensuel b JOIN categorie c ON b.id_categorie = c.id_categorie WHERE b.mois = %s AND b.annee = %s
        """, conn, params=(now.month, now.year))
        
        if not df_enveloppes.empty:
            df_enveloppes['Reste Disponible'] = df_enveloppes['Alloue'] - df_enveloppes['Depense']
            st.dataframe(df_enveloppes, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune enveloppe n'est encore définie pour ce mois.")
            
        st.markdown("---")
        st.subheader("Créer ou réajuster une enveloppe budgétaire")
        if not categories:
            st.warning("Créez d'abord des catégories dans l'onglet Paramétrage.")
        else:
            with st.form("form_env"):
                cat_id = st.selectbox("Sélectionner la catégorie", [c[1] for c in categories])
                alloue = st.number_input("Montant à allouer (FCFA)", min_value=0, step=5000)
                if st.form_submit_button("Allouer ce budget"):
                    real_id = [c[0] for c in categories if c[1] == cat_id][0]
                    
                    cursor.execute("SELECT id_budjet_mensuel FROM budjet_mensuel WHERE id_categorie = %s AND mois = %s AND annee = %s", (real_id, now.month, now.year))
                    exist = cursor.fetchone()
                    if exist:
                        cursor.execute("UPDATE budjet_mensuel SET montant_alloue = %s WHERE id_budjet_mensuel = %s", (alloue, exist[0]))
                    else:
                        cursor.execute("INSERT INTO budjet_mensuel (annee, mois, montant_alloue, id_categorie, id_utilisateur) VALUES (%s, %s, %s, %s, 1)", (now.year, now.month, alloue, real_id))
                    conn.commit()
                    st.success("Allocation enregistrée avec succès !")
                    st.rerun()
        cursor.close()
        conn.close()

#  SAISIE DES REVENUS ET DEPENSES ET CLASSIFICATION AUTOMATIQUE
elif menu == "Saisie & Classification des Flux":
    st.header("Gestion des revenus, dépenses et classification")
    
    conn = obtenir_connexion_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_categorie, nom_categorie FROM categorie")
        cats = cursor.fetchall()
        cursor.execute("SELECT id_compte, nom_compte FROM compte")
        comptes = cursor.fetchall()
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("Ajouter un flux financier")
            if not cats or not comptes:
                st.warning("Veuillez configurer au moins un compte et une catégorie au préalable.")
            else:
                with st.form("form_trans"):
                    m_t = st.number_input("Montant (FCFA)", min_value=0, step=500)
                    d_t = st.text_input("Description / Commerce")
                    t_t = st.selectbox("Type de transaction", ["DEPENSE", "REVENU", "TRANSFERT"])
                    p_t = st.selectbox("Périodicité", ["UNIQUE", "HEBDOMADAIRE", "MENSUEL", "ANNUEL"])
                    cat_t = st.selectbox("Classification Catégorie", [c[1] for c in cats])
                    cpt_t = st.selectbox("Imputation Compte", [cp[1] for cp in comptes])
                    
                    if st.form_submit_button("Valider la transaction"):
                        id_cat = [c[0] for c in cats if c[1] == cat_t][0]
                        id_cpt = [cp[0] for cp in comptes if cp[1] == cpt_t][0]
                        date_now = datetime.now().strftime('%Y-%m-%d')
                        now = datetime.now()
                        
                        cursor.execute("""
                            INSERT INTO transaction (montant, date_transaction, description, type_transaction, id_compte, id_categorie)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (m_t, date_now, d_t, t_t, id_cpt, id_cat))
                        
                        if t_t == "DEPENSE":
                            cursor.execute("UPDATE compte SET solde_actuel = solde_actuel - %s WHERE id_compte = %s", (m_t, id_cpt))
                            cursor.execute("UPDATE budjet_mensuel SET montant_depense = montant_depense + %s WHERE id_categorie = %s AND mois = %s AND annee = %s", (m_t, id_cat, now.month, now.year))
                        elif t_t == "REVENU":
                            cursor.execute("UPDATE compte SET solde_actuel = solde_actuel + %s WHERE id_compte = %s", (m_t, id_cpt))
                        conn.commit()
                        st.success("Flux classé et enregistré !")
                        st.rerun()
                        
        with c2:
            st.subheader("Historique des flux financiers")
            df_t = pd.read_sql_query("""
                SELECT t.date_transaction as Date, t.description as Description, t.type_transaction as Nature, 
                       cp.nom_compte as Compte, c.nom_categorie as Categorie, t.montant as Montant
                FROM transaction t
                JOIN compte cp ON t.id_compte = cp.id_compte
                JOIN categorie c ON t.id_categorie = c.id_categorie ORDER BY t.id_transaction DESC
            """, conn)
            st.dataframe(df_t, use_container_width=True, hide_index=True)
            
        cursor.close()
        conn.close()

#  ASSISTANT FINANCIER INTELLIGENT
elif menu == "Assistant Financier Intelligent":
    st.header("Assistant Financier Intelligent & Coach Décisionnel")
    st.write("Ici, l'application interprète vos chiffres au lieu de simples tableaux statistiques.")
    
    conn = obtenir_connexion_mysql()
    if conn:
        cursor = conn.cursor()
        now = datetime.now()
        df_analyse = pd.read_sql_query("""
            SELECT c.nom_categorie, b.montant_alloue, b.montant_depense 
            FROM budjet_mensuel b JOIN categorie c ON b.id_categorie = c.id_categorie 
            WHERE b.mois = %s AND b.annee = %s
        """, conn, params=(now.month, now.year))
        
        cursor.execute("SELECT titre_projet, montant_cible, montant_actuel_epargne FROM objectif_financier WHERE statut = 'En cours'")
        objectifs = cursor.fetchall()
        
        cursor.execute("SELECT description, montant FROM transaction WHERE type_transaction = 'DEPENSE'")
        factures_rec = cursor.fetchall()
        
        st.markdown("### Alertes Intelligentes & Recommandations")
        alertes_declenchees = 0
        
        if df_analyse.empty:
            st.info("L'Assistant IA attend que tu complètes tes transactions et enveloppes pour pouvoir profiler tes habitudes.")
        else:
            for index, row in df_analyse.iterrows():
                if row['montant_depense'] > row['montant_alloue'] and row['montant_alloue'] > 0:
                    calcul_depassement = ((row['montant_depense'] - row['montant_alloue']) / row['montant_alloue']) * 100
                    st.error(f"Dépassement détecté ({row['nom_categorie']}) : \"Tu dépenses {calcul_depassement:.0f}% de plus en {row['nom_categorie'].lower()} ce mois.\"")
                    alertes_declenchees += 1
                    
                elif row['montant_depense'] >= (row['montant_alloue'] * 0.85) and row['montant_alloue'] > 0:
                    st.warning(f"Alerte Risque Échéance : \"Ton budget {row['nom_categorie'].lower()} risque d'être totalement dépassé avant la fin du mois.\"")
                    alertes_declenchees += 1
                    
            if objectifs:
                for obj in objectifs:
                    reste = obj[1] - obj[2]
                    if reste > 0:
                        st.info(f"Recommandation Stratégique : \"Si tu réduis tes sorties de 10 000 FCFA/semaine, tu alloueras cet excédent à ton projet et tu atteindras ton objectif {obj[0]} précisément 2 mois plus tôt.\"")
                        alertes_declenchees += 1

            if alertes_declenchees == 0:
                st.success("Excellente gestion ce mois-ci ! Aucune anomalie ni dérive de comportement financier n'a été repérée.")
        
        cursor.close()
        conn.close()

# SIMULATEUR DE VIE FINANCIÈRE (PROJECTION ET SCENARIOS)
elif menu == "Simulateur de Vie Financière Future":
    st.header("Simulateur Temporel & Outil de Décision Évolutif")
    st.write("Modélisez des événements de vie futurs pour mesurer leur impact sur votre patrimoine.")
    
    st.markdown("### Ajuster les curseurs du scénario futur")
    sc1, sc2 = st.columns(2)
    with sc1:
        slide_revenu = st.slider("Modification du revenu mensuel de base (FCFA)", min_value=-200000, max_value=500000, value=0, step=10000)
        nouvelle_charge_rec = st.number_input("Ajouter une nouvelle dépense récurrente mensuelle (ex: Crédit, Loyer) (FCFA)", min_value=0, step=5000)
    with sc2:
        slide_epargne = st.slider("Montant d'épargne additionnel mensuel (FCFA)", min_value=-50000, max_value=200000, value=0, step=5000)
        projet_arbitrage = st.text_input("Nom d'un nouveau projet concurrent à tester (ex: Achat Moto, Voyage)", value="")

    st.markdown("---")
    st.subheader("Diagnostic Prédictif du Simulateur")
    
    capacite_epargne_actuelle = max(0, revenu_moyen - total_depense)
    nouvelle_capacite_epargne = capacite_epargne_actuelle + slide_revenu + slide_epargne - nouvelle_charge_rec
    
    if nouvelle_capacite_epargne <= 0 and solde_total > 0:
        st.error(f"Cas 1 — Risque Financier / Rupture : \"Si tu gardes ce rythme de dépenses, ton épargne de sécurité sera entièrement vide dans 5 mois.\"")
        
    elif slide_epargne >= 25000 and nouvelle_charge_rec == 0:
        st.success(f"Cas 2 — Économies futures optimisées : \"Avec {slide_epargne:,.0f} FCFA d'épargne supplémentaire par mois, tu es en mesure de valider ton objectif d'achat prioritaire en décembre.\"")
        
    elif projet_arbitrage != "":
        st.warning(f"Cas 3 — Analyse de Conflit de Projets : \"L'intégration immédiate du projet '{projet_arbitrage}' créera une tension de liquidité qui retardera l'achat ou la réussite de tes autres objectifs de 3 mois.\"")
    else:
        st.info("Fais varier les curseurs ou ajoute un projet pour forcer le simulateur à calculer les scénarios.")

    st.markdown("### Courbe comparative des trajectoires à 12 Mois")
    horizons = [f"Mois +{i}" for i in range(1, 13)]
    
    solde_n = solde_total
    solde_s = solde_total
    list_n = []
    list_s = []
    
    for m in range(12):
        solde_n += capacite_epargne_actuelle
        solde_s += nouvelle_capacite_epargne
        list_n.append(solde_n)
        list_s.append(solde_s)
        
    df_proj = pd.DataFrame({
        'Horizon': horizons,
        'Trajectoire Actuelle (Présent)': list_n,
        'Trajectoire Simulée (Futur)': list_s
    })
    
    st.plotly_chart(px.line(df_proj, x='Horizon', y=['Trajectoire Actuelle (Présent)', 'Trajectoire Simulée (Futur)'], 
                            labels={'value': 'Solde Prévisionnel (FCFA)'}), use_container_width=True)

#  OBJECTIFS FINANCIERS
elif menu == "Objectifs Financiers & Épargne":
    st.header("Suivi des Objectifs d'Épargne & Progression Target")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Fixer un nouvel objectif")
        with st.form("form_obj"):
            t_obj = st.text_input("Intitulé du projet (ex: Ordinateur Portable)")
            c_obj = st.number_input("Montant cible requis (FCFA)", min_value=0, step=10000)
            e_obj = st.number_input("Montant déjà de côté (FCFA)", min_value=0, step=5000)
            d_obj = st.date_input("Date cible souhaitée")
            
            if st.form_submit_button("Valider l'objectif"):
                if t_obj and c_obj > 0:
                    conn = obtenir_connexion_mysql()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO objectif_financier (titre_projet, montant_cible, montant_actuel_epargne, date_cible_souhaitee, id_utilisateur)
                            VALUES (%s, %s, %s, %s, 1)
                        """, (t_obj, c_obj, e_obj, str(d_obj)))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success("Objectif ancré dans le système !")
                        st.rerun()
                    
    with c2:
        st.subheader("Progression de vos objectifs")
        conn = obtenir_connexion_mysql()
        if conn:
            df_o = pd.read_sql_query("SELECT id_objectif_financier as ID, titre_projet, montant_cible, montant_actuel_epargne, date_cible_souhaitee FROM objectif_financier", conn)
            conn.close()
            
            if df_o.empty:
                st.info("Aucun objectif d'épargne défini pour le moment.")
            else:
                for index, row in df_o.iterrows():
                    progress = min(1.0, row['montant_actuel_epargne'] / row['montant_cible'])
                    st.write(f"**{row['titre_projet']}** — {row['montant_actuel_epargne']:,.0f} / {row['montant_cible']:,.0f} FCFA (Cible : {row['date_cible_souhaitee']})")
                    st.progress(progress)
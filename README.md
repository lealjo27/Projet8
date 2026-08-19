# 💳 Déploiement et monitoring d’un modèle de scoring crédit

<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" alt="Python" width="50" height="50"/>
  &nbsp;
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg" alt="PostgreSQL" width="50" height="50"/>
  &nbsp;
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg" alt="Docker" width="50" height="50"/>
  &nbsp;
  <img src="https://cdn.simpleicons.org/gradio/F97316" alt="Gradio" width="50" height="50"/>
  &nbsp;
  <img src="https://cdn.simpleicons.org/streamlit/FF4B4B" alt="Streamlit" width="50" height="50"/>
  &nbsp;
  <img src="https://cdn.simpleicons.org/render/46E3B7" alt="Render" width="50" height="50"/>
</p>

<p align="center">
  <strong>Projet 8 — Formation AI Engineer OpenClassrooms</strong>
</p>

<p align="center">
  Application de scoring crédit, journalisation PostgreSQL, monitoring du data drift et déploiement continu.
</p>

---

## 📋 Table des matières

- [🎯 Présentation](#-présentation)
- [🌐 Applications en ligne](#-applications-en-ligne)
- [✅ Fonctionnalités](#-fonctionnalités)
- [🏗️ Architecture](#️-architecture)
- [🛠️ Technologies utilisées](#️-technologies-utilisées)
- [💻 Application de scoring](#-application-de-scoring)
- [⚖️ Décision de crédit](#️-décision-de-crédit)
- [🗄️ Journalisation PostgreSQL](#️-journalisation-postgresql)
- [⚡ Optimisation des performances](#-optimisation-des-performances)
- [📊 Monitoring](#-monitoring)
- [📈 Simulation du data drift](#-simulation-du-data-drift)
- [📁 Structure du projet](#-structure-du-projet)
- [📦 Installation locale](#-installation-locale)
- [⚙️ Configuration](#️-configuration)
- [▶️ Lancement](#️-lancement)
- [🧪 Tests](#-tests)
- [🐳 Docker](#-docker)
- [🚀 Pipeline CI/CD](#-pipeline-cicd)
- [🔐 Sécurité et RGPD](#-sécurité-et-rgpd)
- [⚠️ Limites](#️-limites)
- [🔭 Perspectives](#-perspectives)
- [👤 Auteur](#-auteur)

---

## 🎯 Présentation

Ce projet fait suite au **Projet 6**, pendant lequel plusieurs modèles de scoring crédit ont été entraînés et comparés.

Les expérimentations ont été suivies avec **MLflow**. Le modèle ayant obtenu les meilleurs résultats selon les métriques définies a été sélectionné pour être mis en production.

Le département fictif **Crédit Express** de l’entreprise **Prêt à Dépenser** souhaite utiliser ce modèle afin d’aider ses collaborateurs à étudier les demandes de crédit.

Le Projet 8 transforme ce modèle expérimental en un service :

- accessible depuis une interface web ;
- testé automatiquement ;
- conteneurisé avec Docker ;
- déployé dans le cloud ;
- journalisé dans PostgreSQL ;
- surveillé grâce à un dashboard de monitoring.

---

## 🌐 Applications en ligne

| Ressource | Accès |
|---|---|
| 💳 Application de scoring Gradio | [Ouvrir l’application](https://projet8-mvym.onrender.com/) |
| 📊 Dashboard Streamlit | [Ouvrir le dashboard](https://m7bijaguzhxwlxcmmoocar.streamlit.app/) |
| 💻 Repository GitHub | [Consulter le code](https://github.com/lealjo27/Projet8/) |

> [!NOTE]
> Les applications utilisent des offres cloud gratuites. Un temps de démarrage peut être nécessaire après une période d’inactivité.

---

## ✅ Fonctionnalités

- ✅ Interface de scoring développée avec Gradio
- ✅ Récupération d’un profil à partir de l’identifiant client
- ✅ Modification des informations de la demande
- ✅ Calcul du score de risque
- ✅ Application d’un seuil de décision
- ✅ Vérification du taux d’endettement
- ✅ Explication de la décision
- ✅ Journalisation dans PostgreSQL / NeonDB
- ✅ Logging exécuté dans un thread d’arrière-plan
- ✅ Dashboard Streamlit et Plotly
- ✅ Comparaison des données de référence et de production
- ✅ Simulation et visualisation d’un data drift
- ✅ Analyse des performances avec `cProfile`
- ✅ Tests automatisés avec `pytest`
- ✅ Conteneurisation avec Docker
- ✅ Pipeline CI/CD avec GitHub Actions
- ✅ Déploiement cloud sur Render

---

## 🏗️ Architecture

### Architecture applicative

```mermaid
flowchart LR
    U[Collaborateur Crédit Express]
    G[Application Gradio]
    P[Préparation des données]
    M[Modèle de scoring]
    R[Score et décision]
    T[ThreadPoolExecutor]
    DB[(PostgreSQL / NeonDB)]
    S[Dashboard Streamlit]

    U --> G
    G --> P
    P --> M
    M --> R
    R --> U
    R --> T
    T --> DB
    DB --> S
```

### Architecture CI/CD

```mermaid
flowchart LR
    A[Push GitHub]
    B[GitHub Actions]
    C[Tests pytest]
    D[Construction Docker]
    E[Déploiement Render]

    A --> B
    B --> C
    C -->|Branche dev| F[Fin du workflow]
    C -->|Branche main| D
    D --> E
```

---

## 🛠️ Technologies utilisées

<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original-wordmark.svg" alt="Python" width="70"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original-wordmark.svg" alt="PostgreSQL" width="70"/>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original-wordmark.svg" alt="Docker" width="70"/>
</p>

| Besoin | Technologie |
|---|---|
| Langage | Python 3.11 |
| Manipulation des données | Pandas et NumPy |
| Modèle de scoring | Scikit-learn / XGBoost |
| Suivi des expérimentations | MLflow |
| Interface de scoring | Gradio |
| Dashboard | Streamlit |
| Visualisations | Plotly |
| Base de données | PostgreSQL / NeonDB |
| Tests | pytest |
| Profiling | cProfile |
| Conteneurisation | Docker |
| Intégration continue | GitHub Actions |
| Déploiement | Render |

---

## 💻 Application de scoring

L’application Gradio permet au collaborateur de saisir ou de modifier :

- l’identifiant du client ;
- le montant du crédit ;
- la durée du crédit ;
- le nombre d’enfants ;
- l’ancienneté professionnelle ;
- l’âge ;
- le revenu annuel.

À partir de l’identifiant client, l’application récupère automatiquement les autres variables nécessaires au modèle.

### Résultats affichés

L’application retourne :

- le score de risque ;
- le seuil de décision ;
- l’accord ou le refus du crédit ;
- la raison de la décision ;
- le taux d’endettement ;
- le temps d’inférence ;
- le temps total de traitement.

### Parcours d’une prédiction

```text
Saisie des informations
        ↓
Récupération du profil client
        ↓
Validation et préparation des variables
        ↓
Calcul du score de risque
        ↓
Vérification du taux d’endettement
        ↓
Affichage de la décision
        ↓
Journalisation dans PostgreSQL
```

---

## ⚖️ Décision de crédit

La décision repose sur deux critères :

1. le score de risque calculé par le modèle ;
2. le taux d’endettement du client.

Le crédit est refusé lorsque :

```text
Score de risque ≥ seuil du modèle
OU
Taux d’endettement > 35 %
```

Dans le cas contraire, le crédit est accordé.

Les principales raisons retournées par l’application sont :

- risque client trop élevé ;
- taux d’endettement trop élevé ;
- critères respectés.

> [!IMPORTANT]
> Dans une véritable application bancaire, le résultat du modèle doit constituer une aide à la décision et faire l’objet d’une validation humaine.

---

## 🗄️ Journalisation PostgreSQL

Chaque prédiction est enregistrée dans une base **PostgreSQL hébergée sur NeonDB**.

### Données enregistrées

- date et heure de la prédiction ;
- identifiant du client ;
- principales informations de la demande ;
- score de risque ;
- seuil utilisé ;
- décision et raison ;
- taux d’endettement ;
- temps d’inférence ;
- latence totale ;
- type de données : référence ou production.

### Logging en arrière-plan

L’écriture dans PostgreSQL est exécutée avec :

```python
ThreadPoolExecutor
```

Le résultat est retourné à l’utilisateur sans attendre la fin de l’appel réseau vers NeonDB.

```text
                      ┌──> Réponse à l’utilisateur
Prédiction terminée ──┤
                      └──> Écriture PostgreSQL en arrière-plan
```

Il s’agit d’une exécution concurrente dans un thread, et non d’une implémentation fondée sur `async/await`.

---

## ⚡ Optimisation des performances

Les performances ont été analysées avec **cProfile** et des benchmarks de latence.

### 1. Optimisation de la recherche client

La première version utilisait un masque booléen Pandas :

```python
client = df.loc[
    df["SK_ID_CURR"] == identifiant_client
].copy()
```

Le DataFrame est désormais indexé avec `SK_ID_CURR` :

```python
client = df_clients_indexe.loc[identifiant_client].copy()
```

### Résultats

| Métrique | Avant | Après | Gain |
|---|---:|---:|---:|
| p50 | 1 908,57 ms | 1 908,55 ms | 0,0 % |
| p95 | 2 157,11 ms | 2 127,17 ms | 1,4 % |
| p99 | 2 730,69 ms | 2 171,12 ms | 20,5 % |

Cette optimisation améliore principalement les requêtes les plus lentes. Plusieurs répétitions restent nécessaires pour confirmer le gain sur le p99.

### 2. Identification du goulot PostgreSQL

Le profiling a montré que l’écriture synchrone dans PostgreSQL représentait la majorité du temps de traitement.

| Étape | Temps | Part |
|---|---:|---:|
| Inférence du modèle | 31 ms | 2,3 % |
| Prédiction complète | 35,16 ms | 2,6 % |
| Logging PostgreSQL | 1 341,83 ms | 97,4 % |
| **Total** | **1 376,99 ms** | **100 %** |

Le principal goulot d’étranglement était donc l’appel réseau vers PostgreSQL, et non le modèle.

### 3. Passage du logging en arrière-plan

Le logging synchrone a été remplacé par une tâche exécutée dans un thread secondaire.

### Gains mesurés

| Métrique | Gain |
|---|---:|
| p50 | 81,5 % |
| p95 | 78,6 % |
| p99 | 76,9 % |

La latence médiane est passée de :

```text
1 908,55 ms → 354,00 ms
```

### Non-régression

L’optimisation ne modifie pas :

- le modèle ;
- les variables transmises ;
- le score calculé ;
- le seuil ;
- le taux d’endettement ;
- les règles de décision.

### Limites

`ThreadPoolExecutor` est adapté à ce POC, mais :

- une écriture peut être perdue si l’application s’arrête brutalement ;
- la file interne peut s’accumuler sous forte charge.

---

## 📊 Monitoring

Le dashboard développé avec **Streamlit** et **Plotly** charge les prédictions enregistrées dans PostgreSQL.

Il permet de surveiller trois dimensions.

### Données

- montant des crédits ;
- revenus ;
- âge ;
- durée du crédit ;
- taux d’endettement ;
- évolution des distributions.

### Métier

- nombre de prédictions ;
- scores de risque ;
- taux d’accord ;
- taux de refus ;
- évolution des décisions.

### Technique

- temps d’inférence ;
- latence totale ;
- latence médiane ;
- percentiles élevés.

Le dashboard compare les données de référence avec les données simulées de production.

---

## 📈 Simulation du data drift

Un data drift a été introduit volontairement pour vérifier la capacité du dashboard à détecter une évolution des données.

### Transformations appliquées

```python
montant_credit_production = montant_credit_reference * 1.50
revenu_production = revenu_reference * 0.85
```

Cela correspond à :

- une augmentation de **50 %** des montants de crédit ;
- une diminution de **15 %** des revenus.

### Objectifs

Cette simulation permet d’observer les effets possibles sur :

- les distributions des variables ;
- le taux d’endettement ;
- les scores de risque ;
- les décisions d’accord ou de refus.

Les comparaisons utilisent notamment :

- des histogrammes normalisés ;
- des distributions cumulées ;
- des graphiques temporels ;
- des indicateurs métier.

> [!NOTE]
> Le drift est simulé pour tester le dispositif de monitoring. Il ne correspond pas à une dérive réelle observée en production.

---

## 📁 Structure du projet

```text
Projet8/
├── .devcontainer/                 # Configuration du conteneur de développement
├── .github/
│   └── workflows/                 # Workflows GitHub Actions
├── credit_app/
│   ├── bdd/                       # Connexion et logging PostgreSQL
│   ├── data/                      # Données clients
│   ├── model/                     # Modèle de scoring
│   ├── scripts/                   # Scripts complémentaires
│   └── predictor.py               # Logique de prédiction
├── notebooks/                     # Analyses et benchmarks
├── tests/                         # Tests automatisés
├── app.py                         # Point d’entrée Render
├── gradio_app.py                  # Interface Gradio
├── dashboard_monitoring.py        # Dashboard Streamlit
├── Dockerfile                     # Image Docker
├── requirements.txt               # Dépendances
├── pyproject.toml                 # Configuration Python
└── README.md                      # Documentation
```

### Fichiers principaux

| Fichier | Rôle |
|---|---|
| `app.py` | Point d’entrée de l’application |
| `gradio_app.py` | Interface utilisateur Gradio |
| `dashboard_monitoring.py` | Dashboard de monitoring |
| `credit_app/predictor.py` | Préparation des données et prédiction |
| `credit_app/bdd/` | Connexion et écriture PostgreSQL |
| `tests/` | Tests automatisés |
| `Dockerfile` | Construction du conteneur |
| `.github/workflows/` | Tests, build et déploiement |

---

## 📦 Installation locale

### Prérequis

- Python 3.11 ;
- Git ;
- une base PostgreSQL ou NeonDB ;
- Docker, si l’application doit être exécutée dans un conteneur.

### 1. Cloner le repository

```bash
git clone https://github.com/lealjo27/Projet8.git
cd Projet8
```

### 2. Créer l’environnement virtuel

#### Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

#### Linux ou macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Créer un fichier `.env` à la racine du projet :

```env
DATABASE_URL=postgresql://utilisateur:mot_de_passe@hote/base?sslmode=require
```

Cette variable doit également être configurée sur :

- Render ;
- Streamlit Community Cloud ;
- GitHub Secrets, si les tests utilisent PostgreSQL.



---

## ▶️ Lancement

### Application Gradio

```bash
python app.py
```

L’application est ensuite disponible sur le port configuré par la variable `PORT`.

### Dashboard Streamlit

```bash
streamlit run dashboard_monitoring.py
```

Le dashboard est généralement disponible à l’adresse :

```text
http://localhost:8501
```

---

## 🧪 Tests

Les tests sont exécutés avec `pytest`.

### Lancer tous les tests

```bash
python -m pytest -v
```

### Lancer les tests avec affichage des sorties

```bash
python -m pytest -v -s
```

Les tests vérifient notamment :

- la fonction de prédiction ;
- la validation des entrées ;
- le format des résultats ;
- les règles de décision ;
- la connexion PostgreSQL ;
- l’enregistrement des prédictions.

Les services externes doivent être simulés avec des mocks lorsque cela est possible afin de rendre les tests reproductibles.

---

## 🐳 Docker

<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original-wordmark.svg" alt="Docker" width="120"/>
</p>

### Construire l’image

```bash
docker build -t projet8-scoring .
```

### Lancer le conteneur

```bash
docker run --rm \
  -p 7860:7860 \
  -e PORT=7860 \
  -e DATABASE_URL="$DATABASE_URL" \
  projet8-scoring
```

L’application est ensuite disponible à l’adresse :

```text
http://localhost:7860
```

---

## 🚀 Pipeline CI/CD

La pipeline est automatisée avec **GitHub Actions**.

### Branche `dev`

```text
Push sur dev
      ↓
Installation des dépendances
      ↓
Exécution des tests
      ↓
Fin du workflow
```

La branche `dev` permet de valider le code sans construire l’image Docker ni déclencher le déploiement.

### Branche `main`

```text
Push sur main
      ↓
Installation des dépendances
      ↓
Exécution des tests
      ↓
Construction de l’image Docker
      ↓
Déploiement sur Render
```

Le déploiement est exécuté uniquement si les tests réussissent.

### Secrets

Les informations sensibles sont stockées dans les **GitHub Secrets** et dans les variables d’environnement des plateformes cloud.

Exemples :

```text
DATABASE_URL
RENDER_DEPLOY_HOOK_URL
```

---

## 🔐 Sécurité et RGPD

Ce projet est un **POC pédagogique** utilisant des données de démonstration.

Une utilisation avec de véritables données clients nécessiterait notamment :

- une authentification des utilisateurs ;
- une gestion des rôles et des autorisations ;
- une politique de conservation des données ;
- une minimisation des informations enregistrées ;
- une procédure d’accès, de rectification et de suppression ;
- une analyse des biais du modèle ;
- une validation humaine de la décision ;
- une analyse d’impact RGPD ;
- un encadrement des fournisseurs cloud ;
- une procédure de gestion des incidents.

### Principaux risques

| Risque | Mesure recommandée |
|---|---|
| Accès non autorisé | Authentification et gestion des rôles |
| Fuite de données | Chiffrement et limitation des accès |
| Conservation excessive | Politique de suppression automatique |
| Décision automatisée | Validation humaine |
| Biais du modèle | Analyse par sous-population |
| Fuite de secrets | Variables d’environnement et GitHub Secrets |

> [!IMPORTANT]
> L’application actuelle ne doit pas être considérée comme prête à traiter de véritables demandes de crédit.

---

## ⚠️ Limites

- Le data drift est simulé.
- Les performances métier réelles ne sont pas disponibles.
- Les services cloud gratuits disposent de ressources limitées.
- Les applications peuvent nécessiter un temps de démarrage.
- Le logging par thread ne garantit pas la persistance des tâches.
- Le dashboard ne déclenche pas encore d’alertes automatiques.
- L’authentification n’est pas encore mise en place.
- La conformité RGPD complète n’est pas implémentée.

---

## 🔭 Perspectives

- Ajouter des alertes automatiques de drift.
- Suivre la performance réelle du modèle.
- Intégrer MLflow Model Registry.
- Automatiser le réentraînement.
- Versionner les modèles déployés.
- Utiliser une file persistante pour le logging.
- Ajouter une authentification.
- Renforcer la sécurité et la conformité RGPD.
- Déployer l’application sur une infrastructure plus robuste.

---

## 👤 Auteur

**Jo — [@lealjo27](https://github.com/lealjo27)**

Projet réalisé dans le cadre de la formation **AI Engineer OpenClassrooms**.

<p align="center">
  <a href="https://github.com/lealjo27/Projet8">
    <img src="https://img.shields.io/badge/GitHub-Projet%208-181717?style=for-the-badge&logo=github" alt="GitHub Projet 8"/>
  </a>
  <a href="https://projet8-mvym.onrender.com/">
    <img src="https://img.shields.io/badge/Gradio-Application-F97316?style=for-the-badge&logo=gradio" alt="Application Gradio"/>
  </a>
  <a href="https://m7bijaguzhxwlxcmmoocar.streamlit.app/">
    <img src="https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit" alt="Dashboard Streamlit"/>
  </a>
</p>

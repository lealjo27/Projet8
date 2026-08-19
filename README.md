# Déploiement et monitoring d’un modèle de scoring crédit

Projet 8 de la formation **AI Engineer d’OpenClassrooms**.

Ce projet fait suite au Projet 6, dans lequel plusieurs modèles de scoring crédit ont été comparés avec **MLflow**. Le modèle ayant obtenu les meilleurs résultats a été sélectionné pour être déployé et monitoré.

Le département fictif **Crédit Express** de l’entreprise **Prêt à Dépenser** souhaite utiliser ce modèle pour assister ses collaborateurs dans l’étude des demandes de crédit.

---

## Applications en ligne

| Application | Accès |
|---|---|
| Application de scoring Gradio | https://projet8-mvym.onrender.com/ |
| Dashboard Streamlit | https://m7bijaguzhxwlxcmmoocar.streamlit.app/ |
| Repository GitHub | https://github.com/lealjo27/Projet8/ |

> Les applications utilisent des offres cloud gratuites. Un délai de démarrage peut être nécessaire après une période d’inactivité.

---

## Objectifs du projet

Le projet consiste à transformer un modèle de machine learning en un service utilisable en production.

Les principaux objectifs sont :

- déployer une application de scoring ;
- afficher un score et une décision compréhensible ;
- enregistrer les prédictions dans PostgreSQL ;
- automatiser les tests et le déploiement ;
- surveiller les données et les performances ;
- détecter une éventuelle dérive des données ;
- mesurer et optimiser la latence de l’application.

---

## Architecture

```mermaid
flowchart LR
    U[Collaborateur Crédit Express]
    G[Application Gradio]
    M[Modèle de scoring]
    R[Score et décision]
    T[ThreadPoolExecutor]
    DB[(PostgreSQL / NeonDB)]
    S[Dashboard Streamlit]

    U --> G
    G --> M
    M --> R
    R --> U
    R --> T
    T --> DB
    DB --> S
```

### Pipeline CI/CD

```mermaid
flowchart LR
    A[Push GitHub]
    B[GitHub Actions]
    C[Tests pytest]
    D[Image Docker]
    E[Déploiement Render]

    A --> B
    B --> C
    C -->|Branche main| D
    D --> E
```

---

## Technologies utilisées

| Besoin | Technologie |
|---|---|
| Langage | Python 3.11 |
| Suivi des expérimentations | MLflow |
| Interface de scoring | Gradio |
| Dashboard | Streamlit et Plotly |
| Base de données | PostgreSQL / NeonDB |
| Tests | pytest |
| Conteneurisation | Docker |
| Intégration continue | GitHub Actions |
| Déploiement | Render |
| Manipulation des données | Pandas et NumPy |

---

## Application de scoring

L’application Gradio permet au collaborateur de saisir :

- l’identifiant du client ;
- le montant du crédit ;
- la durée du crédit ;
- le nombre d’enfants ;
- l’ancienneté professionnelle ;
- l’âge ;
- le revenu annuel.

À partir de l’identifiant client, l’application récupère automatiquement les autres variables nécessaires au modèle.

Elle retourne ensuite :

- le score de risque ;
- le seuil de décision ;
- l’accord ou le refus du crédit ;
- la raison de la décision ;
- le taux d’endettement ;
- le temps d’inférence ;
- le temps total de traitement.

---

## Décision de crédit

La décision dépend de deux critères :

1. le score de risque calculé par le modèle ;
2. le taux d’endettement du client.

Le crédit est refusé si :

```text
score de risque supérieur ou égal au seuil du modèle
OU
taux d’endettement supérieur à 35 %
```

Dans le cas contraire, le crédit est accordé.

> Dans une véritable application bancaire, le résultat du modèle devrait rester une aide à la décision et faire l’objet d’une validation humaine.

---

## Journalisation des prédictions

Chaque prédiction est enregistrée dans une base **PostgreSQL hébergée sur NeonDB**.

Les données enregistrées comprennent notamment :

- l’identifiant du client ;
- la date de la prédiction ;
- les principales informations de la demande ;
- le score de risque ;
- la décision ;
- le taux d’endettement ;
- le temps d’inférence ;
- la latence totale ;
- le type de données : référence ou production.

### Écriture en arrière-plan

L’écriture dans PostgreSQL est exécutée dans un thread d’arrière-plan avec :

```python
ThreadPoolExecutor
```

Le résultat est ainsi retourné à l’utilisateur sans attendre la fin de l’appel réseau vers NeonDB.

```text
Prédiction
├── Réponse immédiate à l’utilisateur
└── Écriture PostgreSQL en arrière-plan
```

Il s’agit d’une exécution concurrente avec un thread, et non d’une implémentation avec `async/await`.

---

## Optimisation des performances

Les performances de l’application ont été analysées avec **cProfile** et des benchmarks de latence.

### Optimisation de la recherche client

La recherche initiale utilisait un masque booléen Pandas :

```python
client = df.loc[
    df["SK_ID_CURR"] == identifiant_client
].copy()
```

Le DataFrame est désormais indexé par identifiant client afin de permettre un accès direct :

```python
client = df_clients_indexe.loc[identifiant_client].copy()
```

Résultats du premier benchmark :

| Métrique | Avant | Après | Gain |
|---|---:|---:|---:|
| p50 | 1 908,57 ms | 1 908,55 ms | 0,0 % |
| p95 | 2 157,11 ms | 2 127,17 ms | 1,4 % |
| p99 | 2 730,69 ms | 2 171,12 ms | 20,5 % |

L’amélioration concerne principalement les requêtes les plus lentes. Plusieurs répétitions sont nécessaires pour confirmer le gain sur le p99.

### Identification du goulot PostgreSQL

Le profiling a montré que l’écriture synchrone dans PostgreSQL représentait la majorité du temps de traitement :

| Étape | Temps | Part |
|---|---:|---:|
| Inférence du modèle | 31 ms | 2,3 % |
| Prédiction complète | 35,16 ms | 2,6 % |
| Logging PostgreSQL | 1 341,83 ms | 97,4 % |
| Total | 1 376,99 ms | 100 % |

Le principal goulot d’étranglement était donc l’appel réseau vers PostgreSQL, et non le modèle.

### Résultats après optimisation

Le passage du logging en arrière-plan a permis d’obtenir :

- une latence médiane passant de **1 908,55 ms à 354,00 ms** ;
- une réduction du p50 de **81,5 %** ;
- une réduction du p95 de **78,6 %** ;
- une réduction du p99 de **76,9 %**.

Cette optimisation ne modifie pas :

- le modèle ;
- les variables utilisées ;
- le score calculé ;
- le seuil ;
- les règles de décision.

### Limites

`ThreadPoolExecutor` est adapté à ce POC, mais :

- une écriture en attente peut être perdue si l’application s’arrête brutalement ;
- la file interne peut s’accumuler en cas de forte charge.

Une application critique pourrait utiliser une file persistante comme **Redis avec Celery ou RQ**.

---

## Monitoring

Le dashboard Streamlit permet de suivre les données enregistrées dans PostgreSQL.

Il permet notamment de surveiller :

- le nombre de prédictions ;
- les scores de risque ;
- les accords et les refus ;
- le montant des crédits ;
- les revenus ;
- le taux d’endettement ;
- le temps d’inférence ;
- la latence applicative ;
- l’évolution des distributions.

Le dashboard compare les données de référence avec les données simulées de production.

---

## Simulation du data drift

Un data drift a été volontairement introduit afin de tester le dashboard de monitoring.

Les transformations appliquées sont :

```python
montant_credit_production = montant_credit_reference * 1.50
revenu_production = revenu_reference * 0.85
```

Cela correspond à :

- une augmentation de **50 %** des montants de crédit ;
- une diminution de **15 %** des revenus.

Cette simulation permet d’observer les effets possibles sur :

- les distributions des variables ;
- le taux d’endettement ;
- les scores de risque ;
- les accords et les refus.

> Le drift est simulé pour tester le dispositif de surveillance. Il ne correspond pas à une dérive réelle observée en production.

---

## Structure du projet

```text
Projet8/
├── .github/workflows/       # Pipeline GitHub Actions
├── credit_app/
│   ├── bdd/                 # Connexion et logging PostgreSQL
│   ├── data/                # Données clients
│   ├── model/               # Modèle de scoring
│   └── predictor.py         # Logique de prédiction
├── notebooks/               # Analyses et expérimentations
├── tests/                   # Tests pytest
├── app.py                   # Point d’entrée
├── gradio_app.py            # Interface Gradio
├── dashboard_monitoring.py  # Dashboard Streamlit
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

Cette organisation correspond aux principaux fichiers et dossiers visibles dans le dépôt. ([github.com](https://github.com/lealjo27/Projet8))

---

## Installation locale

### Prérequis

- Python 3.11 ;
- Git ;
- une base PostgreSQL ou NeonDB ;
- Docker, si vous souhaitez utiliser le conteneur.

### 1. Cloner le projet

```bash
git clone https://github.com/lealjo27/Projet8.git
cd Projet8
```

### 2. Créer un environnement virtuel

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

## Configuration de PostgreSQL

Créer un fichier `.env` à la racine du projet :

```env
DATABASE_URL=postgresql://utilisateur:mot_de_passe@hote/base?sslmode=require
```

Le fichier `.env` ne doit jamais être ajouté au repository Git.

La même variable doit être configurée dans :

- Render ;
- Streamlit Community Cloud ;
- GitHub Secrets, si les tests utilisent PostgreSQL.

---

## Lancement

### Application Gradio

```bash
python app.py
```

### Dashboard Streamlit

```bash
streamlit run dashboard_monitoring.py
```

---

## Tests

Les tests sont exécutés avec `pytest` :

```bash
python -m pytest -v
```

Ils vérifient notamment :

- la prédiction ;
- la validation des entrées ;
- le format des résultats ;
- les règles de décision ;
- la connexion PostgreSQL ;
- l’enregistrement des prédictions.

Les services externes doivent être simulés avec des mocks lorsque cela est possible.

---

## Docker

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

L’application est ensuite accessible à l’adresse :

```text
http://localhost:7860
```

---

## Pipeline CI/CD

La pipeline est automatisée avec GitHub Actions.

### Push sur `dev`

```text
Push sur dev
→ installation des dépendances
→ exécution des tests
→ fin du workflow
```

La branche `dev` ne déclenche pas de déploiement.

### Push sur `main`

```text
Push sur main
→ installation des dépendances
→ tests pytest
→ construction de l’image Docker
→ déploiement sur Render
```

Le déploiement est exécuté uniquement si les tests réussissent.

Les informations sensibles sont stockées dans les **GitHub Secrets** et dans les variables d’environnement des plateformes cloud.

---

## Sécurité et RGPD

Ce projet est un **POC pédagogique** utilisant des données de démonstration.

Une utilisation avec de véritables données clients nécessiterait notamment :

- une authentification des utilisateurs ;
- une gestion des rôles et des autorisations ;
- une durée de conservation définie ;
- une minimisation des données enregistrées ;
- une procédure d’accès, de correction et de suppression ;
- une analyse des biais du modèle ;
- une validation humaine de la décision ;
- une analyse d’impact RGPD ;
- une vérification des fournisseurs cloud et des transferts de données.

> L’application actuelle ne doit pas être considérée comme prête à traiter de véritables demandes de crédit.

---

## Limites

- le data drift est simulé ;
- les performances métier réelles ne sont pas disponibles ;
- les services cloud gratuits ont des ressources limitées ;
- les applications peuvent nécessiter un temps de démarrage ;
- le logging par thread ne garantit pas la persistance des tâches ;
- le dashboard ne déclenche pas encore d’alertes ;
- l’authentification n’est pas encore mise en place.

---

## Perspectives

Les évolutions possibles sont :

- ajouter des alertes automatiques de drift ;
- surveiller la performance réelle du modèle ;
- intégrer MLflow Model Registry ;
- automatiser le réentraînement ;
- utiliser une file persistante pour le logging ;
- ajouter une authentification ;
- renforcer la sécurité et la conformité RGPD ;
- déployer l’application sur une infrastructure plus robuste.

---

## Auteur

Projet réalisé par **Jo - @lealjo27 ** dans le cadre de la formation **AI Engineer OpenClassrooms**.

import pytest

from credit_app.bdd import logger_db


# ------------------------------------------------------------------
# Faux objets PostgreSQL
# ------------------------------------------------------------------

class FauxCurseur:
    """Simule un curseur Psycopg2."""

    def __init__(self):
        self.requete_executee = None
        self.valeurs_executees = None
        self.resultat = ("PostgreSQL NeonDB test",)

    def execute(self, requete, valeurs=None):
        self.requete_executee = requete
        self.valeurs_executees = valeurs

    def fetchone(self):
        return self.resultat

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(
        self,
        type_erreur,
        valeur_erreur,
        traceback,
    ):
        self.close()


class FausseConnexion:
    """Simule une connexion Psycopg2."""

    def __init__(self):
        self.curseur = FauxCurseur()
        self.commit_effectue = False
        self.rollback_effectue = False
        self.fermee = False

    def cursor(self):
        return self.curseur

    def commit(self):
        self.commit_effectue = True

    def rollback(self):
        self.rollback_effectue = True

    def close(self):
        self.fermee = True


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def fausse_connexion(monkeypatch):
    """
    Remplace psycopg2.connect par une fausse connexion.

    Cela évite d'utiliser la vraie base NeonDB pendant les tests.
    """

    connexion = FausseConnexion()

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://utilisateur:test@localhost/test",
    )

    monkeypatch.setattr(
        logger_db.psycopg2,
        "connect",
        lambda *args, **kwargs: connexion,
    )

    return connexion


@pytest.fixture
def resultat_prediction():
    """Retourne un résultat complet compatible avec predictor.py."""

    return {
        "Identifiant client": 100001,
        "Montant du crédit": 200_000.0,
        "Durée du crédit en années": 10.0,
        "Nombre d'enfants": 2,
        "Ancienneté professionnelle en années": 5.0,
        "Âge": 35,
        "Revenu annuel": 60_000.0,
        "Score de risque": 0.12,
        "Seuil de décision": 0.1598,
        "Prédiction": 0,
        "Décision": "crédit accordé",
        "Raison": "Critères respectés",
        "Revenu mensuel": 5_000.0,
        "Montant annuel à rembourser": 20_000.0,
        "Montant mensuel à rembourser": 1_666.67,
        "Taux d'endettement": 0.3333,
        "Taux d'endettement en pourcentage": "33.33 %",
        "Seuil d'endettement": 0.35,
        "Temps d'inférence en ms": 4.25,
        "Latence application ms": 8.50,
    }


# ------------------------------------------------------------------
# Tests de la configuration
# ------------------------------------------------------------------

def test_url_base_absente(monkeypatch):
    """Vérifie l'erreur lorsque DATABASE_URL est absente."""

    monkeypatch.delenv(
        "DATABASE_URL",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="DATABASE_URL",
    ):
        logger_db.obtenir_url_base_donnees()


def test_url_base_presente(monkeypatch):
    """Vérifie la récupération de DATABASE_URL."""

    url_attendue = (
        "postgresql://utilisateur:test@localhost/test"
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        url_attendue,
    )

    assert (
        logger_db.obtenir_url_base_donnees()
        == url_attendue
    )


# ------------------------------------------------------------------
# Test de connexion
# ------------------------------------------------------------------

def test_connection_reussie(fausse_connexion):
    """Vérifie le fonctionnement du test de connexion."""

    resultat = logger_db.test_connection()

    assert resultat is True
    assert fausse_connexion.fermee is True

    assert (
        "SELECT version()"
        in fausse_connexion.curseur.requete_executee
    )


def test_connection_echouee(monkeypatch):
    """Vérifie la gestion d'une erreur de connexion."""

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://test",
    )

    def connexion_en_erreur(*args, **kwargs):
        raise ConnectionError(
            "Connexion impossible"
        )

    monkeypatch.setattr(
        logger_db.psycopg2,
        "connect",
        connexion_en_erreur,
    )

    resultat = logger_db.test_connection()

    assert resultat is False


# ------------------------------------------------------------------
# Test de création de la table
# ------------------------------------------------------------------

def test_creation_table(fausse_connexion):
    """Vérifie la création ou la mise à jour de la table."""

    resultat = (
        logger_db.create_predictions_logs_table()
    )

    assert resultat is True
    assert fausse_connexion.commit_effectue is True
    assert fausse_connexion.fermee is True

    requete = (
        fausse_connexion
        .curseur
        .requete_executee
    )

    # La dernière requête exécutée est ALTER TABLE
    assert "ALTER TABLE prediction_logs" in requete
    assert "nombre_enfants" in requete
    assert "score_risque" in requete
    assert "temps_inference_ms" in requete
    assert "type_donnees" in requete


# ------------------------------------------------------------------
# Test de l'enregistrement
# ------------------------------------------------------------------

def test_log_to_postgres(
    fausse_connexion,
    resultat_prediction,
):
    """Vérifie la requête et les valeurs d'insertion."""

    logger_db.log_to_postgres(
        sk_id=100001,
        amt_credit=200_000.0,
        nbre_annee=10.0,
        result_dict=resultat_prediction,
        type_donnees="reference",
    )

    assert fausse_connexion.commit_effectue is True
    assert fausse_connexion.fermee is True

    requete = (
        fausse_connexion
        .curseur
        .requete_executee
    )

    valeurs = (
        fausse_connexion
        .curseur
        .valeurs_executees
    )

    assert "INSERT INTO prediction_logs" in requete
    assert "score_result" not in requete
    assert "nombre_enfants" in requete
    assert "score_risque" in requete
    assert "type_donnees" in requete

    assert len(valeurs) == 20

    # Premières informations
    assert valeurs[0] == 100001
    assert valeurs[1] == 200_000.0
    assert valeurs[2] == 10.0
    assert valeurs[3] == 2
    assert valeurs[4] == 5.0
    assert valeurs[5] == 35
    assert valeurs[6] == 60_000.0

    # Résultat du modèle
    assert valeurs[7] == 0.12
    assert valeurs[8] == 0.1598
    assert valeurs[9] == 0
    assert valeurs[10] == "crédit accordé"
    assert valeurs[11] == "Critères respectés"

    # Monitoring
    assert valeurs[17] == 4.25
    assert valeurs[18] == 8.50
    assert valeurs[19] == "reference"


def test_log_sans_latence(
    fausse_connexion,
    resultat_prediction,
):
    """La latence peut être absente pour les données de référence."""

    resultat_prediction.pop(
        "Latence application ms"
    )

    logger_db.log_to_postgres(
        sk_id=100001,
        amt_credit=200_000,
        nbre_annee=10,
        result_dict=resultat_prediction,
        type_donnees="reference",
    )

    valeurs = (
        fausse_connexion
        .curseur
        .valeurs_executees
    )

    assert valeurs[18] is None


def test_resultat_prediction_invalide():
    """Vérifie que result_dict doit être un dictionnaire."""

    with pytest.raises(
        TypeError,
        match="dictionnaire",
    ):
        logger_db.log_to_postgres(
            sk_id=100001,
            amt_credit=200_000,
            nbre_annee=10,
            result_dict=None,
        )


# ------------------------------------------------------------------
# Test de la fonction utilitaire
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "valeur, resultat_attendu",
    [
        (None, None),
        (5, 5.0),
        (4.25, 4.25),
        ("8.5", 8.5),
    ],
)
def test_convertir_float_optionnel(
    valeur,
    resultat_attendu,
):
    resultat = (
        logger_db.convertir_float_optionnel(
            valeur
        )
    )

    assert resultat == resultat_attendu

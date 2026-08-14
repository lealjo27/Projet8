import pytest

from credit_app.predictor import (
    SEUIL_ENDETTEMENT,
    df,
    predict_client,
)


# ------------------------------------------------------------------
# Valeurs valides utilisées dans les tests
# ------------------------------------------------------------------

IDENTIFIANT_CLIENT_VALIDE = int(
    df["SK_ID_CURR"].dropna().iloc[0]
)

NOMBRE_ENFANTS_VALIDE = 1
ANCIENNETE_VALIDE = 5
AGE_VALIDE = 35
REVENU_ANNUEL_VALIDE = 60_000


# ------------------------------------------------------------------
# Fonction utilitaire
# ------------------------------------------------------------------

def predire_client(
    sk_id_curr=IDENTIFIANT_CLIENT_VALIDE,
    amt_credit=200_000,
    nbre_annee=10,
    nombre_enfants=NOMBRE_ENFANTS_VALIDE,
    anciennete_professionnelle=ANCIENNETE_VALIDE,
    age=AGE_VALIDE,
    revenu_annuel=REVENU_ANNUEL_VALIDE,
):
    """
    Appelle predict_client avec des valeurs valides par défaut.

    Chaque test peut ainsi modifier uniquement le paramètre
    qu'il souhaite vérifier.
    """

    return predict_client(
        sk_id_curr=sk_id_curr,
        amt_credit=amt_credit,
        nbre_annee=nbre_annee,
        nombre_enfants=nombre_enfants,
        anciennete_professionnelle=anciennete_professionnelle,
        age=age,
        revenu_annuel=revenu_annuel,
    )


# ------------------------------------------------------------------
# Tests du résultat de prédiction
# ------------------------------------------------------------------

def test_prediction_valide():
    resultat = predire_client(
        amt_credit=200_000,
        nbre_annee=10,
    )

    assert isinstance(resultat, dict)

    # Informations saisies dans le formulaire
    assert (
        resultat["Identifiant client"]
        == IDENTIFIANT_CLIENT_VALIDE
    )
    assert resultat["Montant du crédit"] == 200_000
    assert resultat["Durée du crédit en années"] == 10
    assert resultat["Nombre d'enfants"] == NOMBRE_ENFANTS_VALIDE

    assert (
        resultat["Ancienneté professionnelle en années"]
        == ANCIENNETE_VALIDE
    )

    assert resultat["Âge"] == AGE_VALIDE
    assert resultat["Revenu annuel"] == REVENU_ANNUEL_VALIDE

    # Résultat du modèle
    assert 0 <= resultat["Score de risque"] <= 1
    assert resultat["Prédiction"] in (0, 1)

    assert resultat["Décision"] in (
        "crédit accordé",
        "crédit refusé",
    )

    assert resultat["Raison"] in (
        "Critères respectés",
        "Risque client trop élevé",
        "Taux d'endettement trop élevé",
    )

    # Indicateurs financiers
    assert resultat[
        "Montant annuel à rembourser"
    ] == pytest.approx(
        20_000,
        abs=0.01,
    )

    assert resultat[
        "Montant mensuel à rembourser"
    ] == pytest.approx(
        1_666.67,
        abs=0.01,
    )

    assert resultat["Revenu mensuel"] == pytest.approx(
        5_000,
        abs=0.01,
    )

    # Monitoring
    assert resultat["Temps d'inférence en ms"] >= 0


def test_coherence_prediction_decision():
    resultat = predire_client()

    prediction = resultat["Prédiction"]
    decision = resultat["Décision"]

    decision_attendue = (
        "crédit refusé"
        if prediction == 1
        else "crédit accordé"
    )

    assert decision == decision_attendue


def test_coherence_taux_endettement():
    resultat = predire_client(
        amt_credit=200_000,
        nbre_annee=10,
        revenu_annuel=60_000,
    )

    # Calcul attendu :
    # mensualité = 200 000 / 10 / 12
    # revenu mensuel = 60 000 / 12
    taux_attendu = (
        (200_000 / 10 / 12)
        / (60_000 / 12)
    )

    assert resultat[
        "Taux d'endettement"
    ] == pytest.approx(
        taux_attendu,
        abs=0.0001,
    )


def test_refus_taux_endettement():
    resultat = predire_client(
        amt_credit=10_000_000,
        nbre_annee=2,
        revenu_annuel=60_000,
    )

    taux_endettement = resultat["Taux d'endettement"]

    assert taux_endettement > SEUIL_ENDETTEMENT
    assert resultat["Prédiction"] == 1
    assert resultat["Décision"] == "crédit refusé"

    assert (
        resultat["Raison"]
        == "Taux d'endettement trop élevé"
    )


# ------------------------------------------------------------------
# Tests du client
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "identifiant_inconnu",
    [
        -1,
        -999999,
    ],
)
def test_client_inconnu(identifiant_inconnu):
    with pytest.raises(ValueError, match="introuvable"):
        predire_client(
            sk_id_curr=identifiant_inconnu,
        )


# ------------------------------------------------------------------
# Tests des champs obligatoires
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "parametre, message_attendu",
    [
        (
            "sk_id_curr",
            "identifiant client",
        ),
        (
            "amt_credit",
            "montant du crédit",
        ),
        (
            "nbre_annee",
            "durée du crédit",
        ),
        (
            "nombre_enfants",
            "nombre d'enfants",
        ),
        (
            "anciennete_professionnelle",
            "ancienneté professionnelle",
        ),
        (
            "age",
            "âge",
        ),
        (
            "revenu_annuel",
            "revenu annuel",
        ),
    ],
)
def test_champs_obligatoires(
    parametre,
    message_attendu,
):
    parametres = {
        "sk_id_curr": IDENTIFIANT_CLIENT_VALIDE,
        "amt_credit": 200_000,
        "nbre_annee": 10,
        "nombre_enfants": NOMBRE_ENFANTS_VALIDE,
        "anciennete_professionnelle": ANCIENNETE_VALIDE,
        "age": AGE_VALIDE,
        "revenu_annuel": REVENU_ANNUEL_VALIDE,
    }

    parametres[parametre] = None

    with pytest.raises(
        ValueError,
        match=message_attendu,
    ):
        predire_client(**parametres)


# ------------------------------------------------------------------
# Tests des types
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "parametre, valeur_invalide",
    [
        ("sk_id_curr", "abc"),
        ("amt_credit", "abc"),
        ("nbre_annee", "abc"),
        ("nombre_enfants", "abc"),
        ("anciennete_professionnelle", "abc"),
        ("age", "abc"),
        ("revenu_annuel", "abc"),
    ],
)
def test_types_invalides(
    parametre,
    valeur_invalide,
):
    parametres = {
        "sk_id_curr": IDENTIFIANT_CLIENT_VALIDE,
        "amt_credit": 200_000,
        "nbre_annee": 10,
        "nombre_enfants": NOMBRE_ENFANTS_VALIDE,
        "anciennete_professionnelle": ANCIENNETE_VALIDE,
        "age": AGE_VALIDE,
        "revenu_annuel": REVENU_ANNUEL_VALIDE,
    }

    parametres[parametre] = valeur_invalide

    with pytest.raises(
        ValueError,
        match="doivent être numériques",
    ):
        predire_client(**parametres)


# ------------------------------------------------------------------
# Tests du montant du crédit
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "montant_invalide",
    [
        0,
        -1,
        -100_000,
    ],
)
def test_montant_credit_invalide(
    montant_invalide,
):
    with pytest.raises(
        ValueError,
        match="montant du crédit doit être supérieur",
    ):
        predire_client(
            amt_credit=montant_invalide,
        )


# ------------------------------------------------------------------
# Tests de la durée du crédit
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "duree_invalide",
    [
        0,
        -1,
        -5,
    ],
)
def test_duree_credit_invalide(
    duree_invalide,
):
    with pytest.raises(
        ValueError,
        match="durée du crédit doit être supérieure",
    ):
        predire_client(
            nbre_annee=duree_invalide,
        )


# ------------------------------------------------------------------
# Tests du nombre d'enfants
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "nombre_enfants_invalide",
    [
        -1,
        -5,
    ],
)
def test_nombre_enfants_invalide(
    nombre_enfants_invalide,
):
    with pytest.raises(
        ValueError,
        match="nombre d'enfants ne peut pas être négatif",
    ):
        predire_client(
            nombre_enfants=nombre_enfants_invalide,
        )


# ------------------------------------------------------------------
# Tests de l'ancienneté professionnelle
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "anciennete_invalide",
    [
        -1,
        -10,
    ],
)
def test_anciennete_negative(
    anciennete_invalide,
):
    with pytest.raises(
        ValueError,
        match="ancienneté professionnelle ne peut pas être négative",
    ):
        predire_client(
            anciennete_professionnelle=anciennete_invalide,
        )


def test_anciennete_incoherente_avec_age():
    with pytest.raises(
        ValueError,
        match="incohérente avec l'âge",
    ):
        predire_client(
            age=20,
            anciennete_professionnelle=10,
        )


# ------------------------------------------------------------------
# Tests de l'âge
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "age_invalide",
    [
        17,
        0,
        -1,
        101,
        150,
    ],
)
def test_age_invalide(age_invalide):
    with pytest.raises(
        ValueError,
        match="âge doit être compris entre 18 et 100 ans",
    ):
        predire_client(
            age=age_invalide,
        )


@pytest.mark.parametrize(
    "age_valide",
    [
        18,
        35,
        65,
        100,
    ],
)
def test_age_valide(age_valide):
    resultat = predire_client(
        age=age_valide,
        anciennete_professionnelle=0,
    )

    assert resultat["Âge"] == age_valide


# ------------------------------------------------------------------
# Tests du revenu annuel
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "revenu_invalide",
    [
        0,
        -1,
        -50_000,
    ],
)
def test_revenu_annuel_invalide(
    revenu_invalide,
):
    with pytest.raises(
        ValueError,
        match="revenu annuel doit être supérieur",
    ):
        predire_client(
            revenu_annuel=revenu_invalide,
        )

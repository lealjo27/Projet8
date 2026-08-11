import pytest
from credit_app.predictor import predict_client, df


VALID_CLIENT_ID = int(df["SK_ID_CURR"].iloc[0])


def test_prediction_valide():
    result = predict_client(
        sk_id_curr=VALID_CLIENT_ID,
        amt_credit=200_000,
        nbre_annee=10,
    )

    assert result["ID Client"] == VALID_CLIENT_ID
    assert 0 <= result["Taux risque client"] <= 1
    assert result["Prediction"] in [0, 1]
    assert result["decision"] in [
        "crédit accordé",
        "crédit refusé",
    ]
    assert result["Montant mensuel à rembourser"] == 1666.67


def test_client_inexistant():
    with pytest.raises(ValueError, match="introuvable"):
        predict_client(
            sk_id_curr=-1,
            amt_credit=200_000,
            nbre_annee=10,
        )


def test_montant_invalide():
    with pytest.raises(ValueError, match="montant du crédit"):
        predict_client(
            sk_id_curr=VALID_CLIENT_ID,
            amt_credit=0,
            nbre_annee=10,
        )


def test_duree_invalide():
    with pytest.raises(ValueError, match="durée du crédit"):
        predict_client(
            sk_id_curr=VALID_CLIENT_ID,
            amt_credit=200_000,
            nbre_annee=0,
        )

def test_refus_taux_endettement():
    result = predict_client(
        sk_id_curr=VALID_CLIENT_ID,
        amt_credit=10_000_000,
        nbre_annee=2,
    )

    taux = float(
        result["Taux endettement du client"]
        .replace("%", "")
        .strip()
    )

    assert taux > 35
    assert result["Prediction"] == 1
    assert result["decision"] == "crédit refusé"
    assert result["Raison"] == "Taux d'endettement trop élevé"

@pytest.mark.parametrize(
    "sk_id, montant, duree, message",
    [
        (None, 100_000, 10, "identifiant client est obligatoire"),
        (100001, None, 10, "montant du crédit est obligatoire"),
        (100001, 100_000, None, "durée du crédit est obligatoire"),
        (100001, 0, 10, "montant du crédit doit être"),
        (100001, -100, 10, "montant du crédit doit être"),
        (100001, 100_000, 0, "durée du crédit doit être"),
        (100001, 100_000, -5, "durée du crédit doit être"),
        ("abc", 100_000, 10, "doivent être numériques"),
        (100001, "abc", 10, "doivent être numériques"),
        (100001, 100_000, "abc", "doivent être numériques"),
    ],
)
def test_entrees_invalides(sk_id, montant, duree, message):
    with pytest.raises(ValueError, match=message):
        predict_client(sk_id, montant, duree)

def test_client_inconnu():
    with pytest.raises(ValueError, match="introuvable"):
        predict_client(-999999, 100_000, 10)
from credit_app.predictor import df



def test_prediction_valide():
    # Sélectionner un client existant
    client_id = int(df["SK_ID_CURR"].dropna().iloc[0])

    # Exécuter une prédiction
    resultat = predict_client(
        sk_id_curr=client_id,
        amt_credit=100_000,
        nbre_annee=10,
    )

    # Vérifier la structure du résultat
    assert isinstance(resultat, dict)
    assert resultat["ID Client"] == client_id

    # Vérifier les valeurs métier
    assert resultat["Prediction"] in (0, 1)
    assert 0 <= resultat["Taux risque client"] <= 1

    # Vérifier la cohérence prédiction/décision
    decision_attendue = (
        "crédit refusé"
        if resultat["Prediction"] == 1
        else "crédit accordé"
    )
    assert resultat["decision"] == decision_attendue
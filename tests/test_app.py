import pytest
from app.app import predict_client, df


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
    with pytest.raises(ValueError, match="AMT_CREDIT"):
        predict_client(
            sk_id_curr=VALID_CLIENT_ID,
            amt_credit=0,
            nbre_annee=10,
        )


def test_duree_invalide():
    with pytest.raises(ValueError, match="NOMBRE_ANNEE"):
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

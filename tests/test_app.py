import pytest
from app.app import predict_client, df


VALID_CLIENT_ID = int(df["SK_ID_CURR"].iloc[0])


def test_prediction_valide():
    result = predict_client(
        sk_id_curr=VALID_CLIENT_ID,
        amt_credit=200_000,
        nbre_annee=10,
    )

    assert result["sk_id_curr"] == VALID_CLIENT_ID
    assert 0 <= result["risk_probability"] <= 1
    assert result["prediction"] in [0, 1]
    assert result["decision"] in [
        "crédit accordé",
        "crédit refusé",
    ]
    assert result["montant_mensuel"] == 1666.67


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

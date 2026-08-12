import os
import pytest
import psycopg2
from credit_app.bdd.logger_db import create_predictions_logs_table, log_to_postgres

DATABASE_URL = os.getenv("DATABASE_URL")


@pytest.fixture(scope="module", autouse=True)
def setup_db():
  """S'assure que la table existe avant de lancer les tests de BDD."""
  create_predictions_logs_table()


def test_database_connection():
  """Vérifie que la connexion à NeonDB fonctionne."""
  assert DATABASE_URL is not None, "La variable DATABASE_URL n'est pas définie"
  try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    result = cur.fetchone()
    cur.close()
    conn.close()
    assert result[0] == 1
  except Exception as e:
    pytest.fail(f"La connexion à la base de données a échoué : {e}")


def test_log_to_postgres():
  """Vérifie qu'on peut insérer un log de test sans erreur."""
  test_sk_id = 999999
  test_amt_credit = 50000.0
  test_nbre_annee = 5.0
  test_result_dict = {
      "Taux risque client": 0.12,
      "Prediction": 0,
      "decision": "test_unit",
  }

  try:
    # Exécution de la fonction d'insertion
    log_to_postgres(
        sk_id=test_sk_id,
        amt_credit=test_amt_credit,
        nbre_annee=test_nbre_annee,
        result_dict=test_result_dict,
    )

    # Vérification que la ligne a bien été insérée dans NeonDB
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        "SELECT sk_id_curr, score_result FROM prediction_logs WHERE"
        " sk_id_curr = %s;",
        (test_sk_id,),
    )
    row = cur.fetchone()

    # Nettoyage de la ligne de test après vérification
    cur.execute(
        "DELETE FROM prediction_logs WHERE sk_id_curr = %s;", (test_sk_id,)
    )
    conn.commit()

    cur.close()
    conn.close()

    assert row is not None, "Le log inséré n'a pas été trouvé en base"
    assert row[0] == test_sk_id

  except Exception as e:
    pytest.fail(
        f"Erreur lors du test d'insertion/lecture des logs en BDD : {e}"
    )
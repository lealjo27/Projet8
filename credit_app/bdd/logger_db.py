import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL")

def log_to_postgres(sk_id, amt_credit, nbre_annee, result_dict):
    # Utilisez os.getenv pour sécuriser vos accès sur Render/Local
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    
    query = """
    INSERT INTO prediction_logs (sk_id_curr, amt_credit, nbre_annee, score_result)
    VALUES (%s, %s, %s, %s)
    """
    cur.execute(query, (sk_id, amt_credit, nbre_annee, psycopg2.extras.Json(result_dict)))
    
    conn.commit()
    cur.close()
    conn.close()

def test_connection():
  """Teste la connexion à NeonDB et affiche le résultat"""
  if not DATABASE_URL:
    print("❌ Erreur : La variable d'environnement DATABASE_URL n'est pas définie.")
    return False

  try:
    # Tentative de connexion
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Exécution d'une requête simple pour valider l'échange
    cur.execute("SELECT version();")
    db_version = cur.fetchone()

    print(f"✅ Connexion à NeonDB réussie ! Version : {db_version[0]}")

    cur.close()
    conn.close()
    return True

  except Exception as e:
    print(f"❌ Échec de la connexion à NeonDB : {e}")
    return False



def create_predictions_logs_table():
  """Crée la table 'prediction_logs' avec un champ JSONB si elle n'existe pas."""
  if not DATABASE_URL:
    print("❌ Erreur : La variable d'environnement DATABASE_URL n'est pas définie.")
    return

  try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Requête de création de table avec score_result au format JSONB
    create_table_query = """
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sk_id_curr INT,
            amt_credit FLOAT,
            nbre_annee FLOAT,
            score_result JSONB
        );
        """

    cur.execute(create_table_query)
    conn.commit()

    cur.close()
    conn.close()
    print("✅ Table 'prediction_logs' créée ou vérifiée avec succès sur NeonDB.")

  except Exception as e:
    print(f"❌ Erreur lors de la création de la table : {e}")


# Si vous exécutez ce fichier directement pour tester
if __name__ == "__main__":
  test_connection()
  


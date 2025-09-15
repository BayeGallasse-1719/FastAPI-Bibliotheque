import psycopg2

def create_database():
    try:
        # Connexion a postgresql avec la base par defaut
        conn = psycopg2.connect(
            host='localhost',
            user='postgres',
            password='p@ssp@ss',
            port=5432,
            dbname='postgres'
        )
     
        cursor = conn.cursor()

        # verification
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'bibliotheque'")
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("CREATE DATABASE bibliotheque;")
            conn.commit()
            print("Base de donnees 'bibliotheque' cree")
        else:
            print("La base de donnees 'bibliotheque' existe deja")

    except psycopg2.Error as e:
        print(f"Erreur lors de la creation de la base : {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def DB_CONFIG():
    try:
        return psycopg2.connect(
            host = 'localhost',
            user = 'postgres',
            dbname = 'bibliotheque',
            password = 'p@ssp@ss',
            port = 5432
        )
    except psycopg2.errors as e:
        print(f"Erreur de connexion a la base de donnee {e}")


def create_tables():
    try:
        conn = DB_CONFIG()
        cursor = conn.cursor()

        # Creation des tables
        cursor.execute("""CREATE TABLE IF NOT EXISTS auteurs(
            id_auteur SERIAL PRIMARY KEY,
            nom_auteur VARCHAR(100) NOT NULL,
            prenom_auteur VARCHAR(100) NOT NULL,
            nationalite VARCHAR(100) NOT NULL);""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS livres(
            id_livre SERIAL PRIMARY KEY,
            titre VARCHAR(100) NOT NULL,
            annee_publication DATE NOT NULL,
            auteur_id INT REFERENCES auteurs(id_auteur));""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS adherents(
            id_adherent SERIAL PRIMARY KEY,
            nom_adherent VARCHAR(100) NOT NULL,
            prenom_adherent VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            date_inscription TIMESTAMP,
            password VARCHAR(200) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE);""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS emprunts(
            id_emprunt SERIAL PRIMARY KEY,
            livre_id INT REFERENCES livres(id_livre) NOT NULL,
            adherent_id INT REFERENCES adherents(id_adherent) NOT NULL,
            date_emprunt TIMESTAMP,
            date_retour DATE );""")
        conn.commit()
        print("Tables creees avec succes.")

    except psycopg2.Error as e:
        print(f"Erreur lors de la creation des tables : {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



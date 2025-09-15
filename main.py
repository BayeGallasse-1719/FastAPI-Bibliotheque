from fastapi import FastAPI, HTTPException, Depends
from database import DB_CONFIG, create_database, create_tables
from shema import AdherentResponse, CreateAdherent, UpdateAdherent
from authentification import get_pwd_hash, verify_pwd, create_acces_token, get_adherent_active
from shema import Token
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from shema import AuteurResponse, AuteurUpdate, CreateAuteur, TableauBord
from shema import LivreResponse, CreateLivre, CreateEmprunt, EmpruntResponse

app = FastAPI(title='FastApi Bibliotheque')
        
create_database()
create_tables()
conn = DB_CONFIG()
cursor = conn.cursor()

# route authentification
@app.post('/register', response_model=AdherentResponse, tags=['Authentification'])
async def register_adh(adherent: CreateAdherent):
    cursor.execute("SELECT 1 FROM adherents WHERE email=%s", (adherent.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail='Email deja utilise')

    hashed_password = get_pwd_hash(adherent.password)
    query = """
        INSERT INTO adherents (nom_adherent, prenom_adherent, email, password)
        VALUES(%s, %s, %s, %s)
        RETURNING id_adherent, nom_adherent, prenom_adherent, email, date_inscription, is_active;
    """
    cursor.execute(query, (adherent.nom_adherent, adherent.prenom_adherent, adherent.email, hashed_password))
    new_adherent = cursor.fetchone()
    return AdherentResponse(
        id_adherent=new_adherent[0],
        nom_adherent=new_adherent[1],
        prenom_adherent=new_adherent[2],
        email=new_adherent[3],
        is_active=new_adherent[4]
    )


@app.post('/token', response_model=Token, tags=['Authentification'])
async def login_acces_token(form_data: OAuth2PasswordRequestForm = Depends()):
    query = """SELECT email, password, is_active FROM adherents WHERE email=%s;"""
    cursor.execute(query, (form_data.username,))
    adherent = cursor.fetchone()
    if not adherent or not verify_pwd(form_data.password, adherent[1]):
        raise HTTPException(status_code=401, detail='Email ou mot de passe incorrect')
    if not adherent[2]:
        raise HTTPException(status_code=403, detail='Adherent inactif')
    access_token = create_acces_token(data={'sub': adherent[0]})
    return {'access_token': access_token, 'token_type': "bearer"}


# route de test
@app.get('/', tags=['Test'])
async def root():
    return {'message': 'FastApi Bibliotheque Avec Authentification'}


@app.get('/profile', response_model=AdherentResponse, tags=['Profile'])
async def get_profile(current_adhent: CreateAdherent=Depends(get_adherent_active)):
    return current_adhent

#-----------------------------------------------------------------------------------
    # CRUD AAdherent
#-----------------------------------------------------------------------------------

@app.get('/adherents', response_model=List[AdherentResponse], tags=['Adherents'])
async def get_adherent(current_adherent: AdherentResponse=Depends(get_adherent_active)):
    cursor.execute("""SELECT id_adherent, nom_adherent, prenom_adherent, email, is_active
                           FROM adherents """)
    adherents = cursor.fetchall()
    return [
        AdherentResponse(
            id_adherent=adherent[0],
            nom_adherent=adherent[1],
            prenom_adherent=adherent[2],
            email=adherent[3], 
            is_active=bool(adherent[4])
        )
        for adherent in adherents
    ]


@app.get('/adherents/{id_adherent}', response_model=AdherentResponse, tags=['Adherents'])
async def get_adherent_by_id(id_adherent:int, current_adherent:AdherentResponse=Depends(get_adherent_active)):
    cursor.execute("""SELECT id_adherent, nom_adherent, prenom_adherent, email, is_active
                           FROM adherents WHERE id_adherent=%s;""",(id_adherent,))
    adherent = cursor.fetchone()
    
    return AdherentResponse(
            id_adherent=adherent[0],
            nom_adherent=adherent[1],
            prenom_adherent=adherent[2],
            email=adherent[3], 
            is_active=bool(adherent[4])
        )


@app.post('/adherents', response_model=AdherentResponse, tags=['Adherents'])
async def create_adherent(adherent:CreateAdherent, current_adherent:AdherentResponse=Depends(get_adherent_active)):
    cursor.execute("SELECT 1 FROM adherents WHERE email=%s", (adherent.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail='Adherent existe dejas')

    hashed_password = get_pwd_hash(adherent.password)
    query = """
        INSERT INTO adherents (nom_adherent, prenom_adherent, email, password)
        VALUES(%s, %s, %s, %s)
        RETURNING id_adherent, nom_adherent, prenom_adherent, email, is_active;
    """
    cursor.execute(query, (adherent.nom_adherent, adherent.prenom_adherent, adherent.email, hashed_password))
    new_adherent = cursor.fetchone()
    return AdherentResponse(
        id_adherent=new_adherent[0],
        nom_adherent=new_adherent[1],
        prenom_adherent=new_adherent[2],
        email=new_adherent[3],
        is_active=new_adherent[4]
    )


@app.put("/adherents/{id_adherent}", response_model=AdherentResponse, tags=["Adherents"])
async def update_adh_by_id(
    id_adherent: int,
    adherent: UpdateAdherent,
    current_adherent: AdherentResponse = Depends(get_adherent_active)):

    cursor.execute("SELECT id_adherent FROM adherents WHERE id_adherent=%s", (id_adherent,))
    exist_adherent = cursor.fetchone()
    if not exist_adherent:
        raise HTTPException(status_code=404, detail="Adherent n'existe pas")

    query = """
        UPDATE adherents
        SET nom_adherent=%s,
            prenom_adherent=%s,
            email=%s,
            password=%s,
            is_active=%s
        WHERE id_adherent=%s
    """
    cursor.execute(query, (
        adherent.nom_adherent,
        adherent.prenom_adherent,
        adherent.email,
        get_pwd_hash(adherent.password), 
        adherent.is_active,
        id_adherent
    ))
    conn.commit()

    cursor.execute("""
        SELECT id_adherent, nom_adherent, prenom_adherent, email, is_active
        FROM adherents
        WHERE id_adherent=%s
    """, (id_adherent,))
    updated = cursor.fetchone()

    return AdherentResponse(
        id_adherent=updated[0],
        nom_adherent=updated[1],
        prenom_adherent=updated[2],
        email=updated[3],
        is_active=updated[4]
    )


@app.delete('/adherents/delete/{id_adherent}', response_model=AdherentResponse, tags=['Adherents'])
async def delete_adherent_by_id(id_adherent: int,
    current_adherent: AdherentResponse = Depends(get_adherent_active)):
    
    cursor.execute("""
        SELECT id_adherent, nom_adherent, prenom_adherent, email, is_active
        FROM adherents
        WHERE id_adherent=%s
    """, (id_adherent,))
    exist_adherent = cursor.fetchone()
    if not exist_adherent:
        raise HTTPException(status_code=404, detail="Adherent n'existe pas")
    query = "DELETE FROM adherents WHERE id_adherent=%s;"
    cursor.execute(query, (id_adherent,))
    conn.commit()
    return AdherentResponse(
            id_adherent=exist_adherent[0],
            nom_adherent=exist_adherent[1],
            prenom_adherent=exist_adherent[2],
            email=exist_adherent[3],
            is_active=exist_adherent[4]
        )

#-----------------------------------------------------------------------------------
    # CRUD Auteur
#-----------------------------------------------------------------------------------

@app.get('/auteurs', response_model=List[AuteurResponse], tags=['Auteurs'])
async def get_auteurs(current_adherent: AdherentResponse=Depends(get_adherent_active)):
    cursor.execute("""SELECT id_auteur, nom_auteur, prenom_auteur, nationalite
                   FROM auteurs""")
    auteurs = cursor.fetchall()
    if not auteurs:
        raise HTTPException(status_code=404, detail='Aucun Auteur Trouve')
    return [AuteurResponse(
                id_auteur=auteur[0],
                nom_auteur=auteur[1],
                prenom_auteur=auteur[2],
                nationalite=auteur[3]
            )for auteur in auteurs
        ]

@app.post('/auteurs', response_model=AuteurResponse, tags=['Auteurs'])
async def create_auteur(auteur:CreateAuteur, 
                current_adherent:AdherentResponse=Depends(get_adherent_active)):
    
    cursor.execute("""INSERT INTO auteurs(nom_auteur, prenom_auteur, nationalite)
                   VALUES(%s, %s, %s) RETURNING id_auteur, nom_auteur, prenom_auteur, nationalite;""",
                   (auteur.nom_auteur, auteur.prenom_auteur, auteur.nationalite))
    auteur_cree = cursor.fetchone()
    conn.commit()
    
    return AuteurResponse(
        id_auteur=auteur_cree[0],
        nom_auteur=auteur_cree[1],
        prenom_auteur=auteur_cree[2],
        nationalite=auteur_cree[3]
    )

@app.get('/auteurs/{id_auteur}', response_model=AuteurResponse, tags=['Auteurs'])
async def get_auteur_by_id(id_auteur:int, 
                    current_adherent:AdherentResponse=Depends(get_adherent_active)):
    
    cursor.execute("""SELECT id_auteur, nom_auteur, prenom_auteur, nationalite
                   FROM auteurs WHERE id_auteur=%s;""",(id_auteur,))
    auteur = cursor.fetchone()
    if not auteur:
        raise HTTPException(status_code=404, detail='Auteur Introuvable')
    return AuteurResponse(
        id_auteur=auteur[0],
        nom_auteur=auteur[1],
        prenom_auteur=auteur[2],
        nationalite=auteur[3]
    )

@app.delete('/auteurs/delete/{id_auteur}', response_model=AuteurResponse, tags=['Auteurs'])
async def delete_auteur_by_id(id_auteur:int,
            current_adherent:AdherentResponse=Depends(get_adherent_active)):
    cursor.execute("""SELECT id_auteur, nom_auteur, prenom_auteur, nationalite
                   FROM auteurs WHERE id_auteur=%s;""",(id_auteur,))
    exist_auteur = cursor.fetchone()
    if not exist_auteur:
        raise HTTPException(status_code=404, detail='Auteur Introuvable')
    
    cursor.execute("""DELETE FROM auteurs WHERE id_auteur=%s;""",(id_auteur,))
    conn.commit()

    return AuteurResponse(
        id_auteur=exist_auteur[0],
        nom_auteur=exist_auteur[1],
        prenom_auteur=exist_auteur[2],
        nationalite=exist_auteur[3]
    )


#-----------------------------------------------------------------------------------
    # CRUD Livre
#-----------------------------------------------------------------------------------

@app.get('/livres', response_model=List[LivreResponse], tags=['Livres'])
async def get_livre(current_adherent:AdherentResponse=Depends(get_adherent_active)):
    cursor.execute("""SELECT id_livre, titre, annee_publication, A.nom_auteur, A.prenom_auteur
                   FROM livres JOIN auteurs as A ON A.id_auteur = auteur_id;""")
    livres = cursor.fetchall()
    if not livres:
        raise HTTPException(status_code=404, detail='Aucun livre trouve')

    return [LivreResponse(
        id_livre=livre[0],
        titre=livre[1],
        annee_publication=livre[2],
        nom_auteur=livre[3],
        prenom_auteur=livre[4]
    ) for livre in livres]

@app.post('/livres', response_model=LivreResponse, tags=['Livres'])
async def create_livre(livre: CreateLivre, 
                current_adherent:CreateAdherent=Depends(get_adherent_active)):
    
    cursor.execute("""SELECT nom_auteur, prenom_auteur FROM auteurs
                WHERE id_auteur = %s""", (livre.auteur_id,))
    auteur_exist = cursor.fetchone()

    if not auteur_exist:
        raise HTTPException(status_code=401, detail='Auteur Livre Introuvable')

    cursor.execute("""INSERT INTO livres(titre, annee_publication, auteur_id)
                VALUES (%s, %s, %s) RETURNING id_livre, titre, annee_publication;""", 
                (livre.titre, livre.annee_publication, livre.auteur_id))
    livre_cree = cursor.fetchone()
    conn.commit() 
    
    return LivreResponse(
        id_livre=livre_cree[0],
        titre=livre_cree[1],
        annee_publication=livre_cree[2],
        nom_auteur=auteur_exist[0],
        prenom_auteur=auteur_exist[1]
    )
   
#-----------------------------------------------------------------------------------
    # CRUD Emprunt
#-----------------------------------------------------------------------------------
@app.get('/emprunts', response_model=List[EmpruntResponse], tags=['Emprunts'])
async def get_emprunt(current_adherent:AdherentResponse=Depends(get_adherent_active)):
    query = """SELECT id_emprunt, date_emprunt, date_retour, L.titre,
            A.nom_adherent, A.prenom_adherent FROM emprunts
            JOIN livres as L ON L.id_livre=livre_id
            JOIN adherents as A ON A.id_adherent=adherent_id;"""
    cursor.execute(query)
    exist_emprunt = cursor.fetchall()
    if not exist_emprunt:
        raise HTTPException(status_code=404, detail='Aucun Emprunt Enregistrer')

    return [EmpruntResponse(
        id_emprunt=emprunt[0],
        date_emprunt=emprunt[1],
        date_retour=emprunt[2],
        titre=emprunt[3],
        nom_adherent=emprunt[4],
        prenom_adherent=emprunt[5]
    )for emprunt in exist_emprunt]

@app.post('/emprunts', response_model=EmpruntResponse, tags=['Emprunts'])
async def create_emprunt(emprunt:CreateEmprunt, 
            current_adherent:AdherentResponse=Depends(get_adherent_active)):
    
    cursor.execute("""SELECT titre FROM livres WHERE id_livre=%s;""", (emprunt.livre_id,))
    exist_livre = cursor.fetchone()
    cursor.execute("SELECT nom_adherent, prenom_adherent FROM adherents WHERE id_adherent=%s",(emprunt.adherent_id,))
    exist_adherent = cursor.fetchone()

    if not exist_livre or not exist_adherent:
        raise HTTPException(status_code=404, detail='Livre ou Adherent Introuvable')
    
    cursor.execute("""INSERT INTO emprunts(livre_id, adherent_id, date_emprunt, date_retour)
                    VALUES (%s, %s, %s, %s) RETURNING id_emprunt, date_retour, date_emprunt;""", 
                    (emprunt.livre_id, emprunt.adherent_id, emprunt.date_emprunt, emprunt.date_retour))
    emprunt_cree = cursor.fetchone()
    conn.commit()

    return EmpruntResponse(
        id_emprunt=emprunt_cree[0],
        titre=exist_livre[0],
        nom_adherent=exist_adherent[0],
        prenom_adherent=exist_adherent[1],
        date_emprunt=emprunt_cree[2],
        date_retour=emprunt_cree[1]
    )


#-----------------------------------------------------------------------------------
    # Tableau de bord
#-----------------------------------------------------------------------------------
@app.get('/tableau_bord',response_model=TableauBord, tags=['Tableau De Bord'])
async def tableau_bord(current_adherent:AdherentResponse=Depends(get_adherent_active)):
    cursor.execute("""SELECT COUNT(id_adherent) FROM adherents;""")
    nbre_adherent = cursor.fetchone()
    
    cursor.execute("""SELECT COUNT(id_livre) FROM livres;""")
    nbre_livre = cursor.fetchone()

    cursor.execute("SELECT COUNT(livre_id) FROM emprunts;")
    nbre_livre_emp = cursor.fetchone()

    return TableauBord(
        nbre_adherent=nbre_adherent[0],
        nbre_livre=nbre_livre[0],
        nbre_livre_emprunte=nbre_livre_emp[0]
    )


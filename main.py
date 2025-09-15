from fastapi import FastAPI, HTTPException, Depends
from database import DB_CONFIG, create_database, create_tables
from shema import AdherentResponse, CreateAdherent, UpdateAdherent
from authentification import get_pwd_hash, verify_pwd, create_acces_token, get_adherent_active
from shema import Token
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

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


# route CRUD Adherent
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


from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional

# Modele Auteur
class CreateAuteur(BaseModel):
    nom: str = Field(..., alias="nom_auteur")
    prenom: str = Field(..., alias="prenom_auteur")
    nationalite: str

    class Config:
        allow_population_by_field_name = True

class AuteurResponse(BaseModel):
    id_auteur: int
    nom: str = Field(..., alias="nom_auteur")
    prenom: str = Field(..., alias="prenom_auteur")
    nationalite: str

    class Config:
        from_attributes = True  

# Modele livre
class CreateLivre(BaseModel):
    titre: str
    annee_publication: date
    auteur_id: int

    class Config:
        allow_population_by_field_name = True

class LivreResponse(BaseModel):
    id_livre: int
    titre: str
    annee_publication: date
    auteur_id: int

    class Config:
        from_attributes = True

# Modele Adherent
class CreateAdherent(BaseModel):
    nom_adherent: str 
    prenom_adherent: str 
    email: EmailStr
    password: str
    date_inscription: date
    is_active: bool

    class Config:
        allow_population_by_field_name = True

class UpdateAdherent(BaseModel):
    nom_adherent: Optional[str] 
    prenom_adherent: Optional[str] 
    email: Optional[EmailStr]
    password: Optional[str]
    date_inscription: Optional[date]
    is_active: Optional[bool]

    class Config:
        allow_population_by_field_name = True

class AdherentResponse(BaseModel):
    id_adherent: int
    nom_adherent: str 
    prenom_adherent: str 
    email: EmailStr
    #date_inscription: date
    is_active: bool

    class Config:
        from_attributes = True

# Modele Emprunt
class CreateEmprunt(BaseModel):
    livre_id: int
    adherent_id: int
    date_emprunt: date
    date_retour: Optional[date] = None

    class Config:
        allow_population_by_field_name = True

class EmpruntResponse(BaseModel):
    id_emprunt: int
    livre_id: int
    adherent_id: int
    date_emprunt: date
    date_retour: Optional[date] = None

    class Config:
        from_attributes = True

# modele Token
class AdherentLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token : str
    token_type : str

class TokenData(BaseModel):
    email : EmailStr
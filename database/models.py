'''
This module defines the database models for the application.'''

import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()

class Regla(Base):
    '''
    Representa una regla en la base de datos.
    
    Atributos:
        regla_id (int): The unique identifier for the rule.
        texto_regla (str): el texto de la regla como fue ingresada por el usuario.
        fecha_creacion (datetime): The date when the rule was created.
    '''
    __tablename__ = 'reglas'
    
    regla_id = Column(Integer, primary_key=True, autoincrement=True)
    texto_regla = Column(String, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False)

    def __init__(self, texto_regla: str):
        self.texto_regla = texto_regla
        
    def __repr__(self):
        return f"<Regla(regla_id={self.regla_id}, texto_regla='{self.texto_regla}', fecha_creacion='{self.fecha_creacion}')>"
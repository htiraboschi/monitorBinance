import json
from fastapi import FastAPI, HTTPException, Depends, Response, status, Query
from pydantic import BaseModel
from api.dependencies import get_db
from database.crud import create_regla, get_reglas, delete_regla, get_regla_by_id
from database.models import Regla
from bot.monitorBinance import validar_en_binance, create_binance_instance

# Ruta al archivo JSON
config_file = './config.json'

app = FastAPI()
with open(config_file, 'r') as file:
    config_data = json.load(file)        
    api_key = config_data["binance_conection"]["API_KEY"]
    api_secret = config_data["binance_conection"]["API_SECRET"]
binance = create_binance_instance(api_key, api_secret)

class ReglaRequest(BaseModel):
    texto_regla: str

    class Config:
        from_attributes = True  # Necesario para compatibilidad con SQLAlchemy (antes `orm_mode = True`)

#obtener listado de reglas
@app.get("/reglas", status_code=status.HTTP_200_OK, tags= ['reglas'])
async def get_reglas_from_db(db = Depends(get_db), response: Response = Response()):
    '''
    Description:
    Obtiene listado de reglas desde la base de datos.
    '''
    
    try:
        reglas = await get_reglas(db)
        response.status_code = status.HTTP_200_OK
        return {"cantidad de reglas": len(reglas)}
    except HTTPException as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": str(e)}

#validar una regla
@app.get("/regla_validation/", status_code=status.HTTP_200_OK, tags= ['reglas'])
async def get_regla_validation(texto_regla: str = Query(None,title="Texto de la regla", description="Texto que representa la regla a validar"), response: Response = Response()):
    '''
    Description:
    Valida una regla.
    '''
    
    try:
        validation = validar_en_binance(binance,texto_regla)
        response.status_code = status.HTTP_200_OK
        return {"validacion": validation}
    except HTTPException as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": str(e)}

#insertar una regla
@app.post("/reglas", status_code=status.HTTP_201_CREATED, tags= ['reglas'])
async def create_regla_in_db(regla: ReglaRequest, db = Depends(get_db), response: Response = Response()):
    '''
    Description:
    Inserta una regla en la base de datos.
    '''
    
    try:
        validation = validar_en_binance(binance,regla.texto_regla)
        if not validation:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "La regla no es valida"}
        else:
            regla = await create_regla(db, Regla(**regla.model_dump()))
            response.status_code = status.HTTP_201_CREATED
            return {"regla": regla}
    except HTTPException as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": str(e)}
    
    
#borrar una regla
@app.delete("/reglas/", status_code=status.HTTP_200_OK, tags= ['reglas'])
async def delete_regla_in_db(regla_id: int = Query(None, title="ID de la regla", description="ID de la regla a eliminar"), db = Depends(get_db), response: Response = Response()):
    '''
    Description:
    Elimina una regla de la base de datos.
    '''
    
    try:
        regla = await get_regla_by_id(db, regla_id)
        if not regla:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"error": "La regla no existe"}
        else:
            await delete_regla(db, regla)
            response.status_code = status.HTTP_200_OK
            return {"resultado": f"regla {regla_id} eliminada"}
    except HTTPException as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": str(e)}  
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import React, {useEffect, useState} from 'react'

const BASE_URL = 'http://192.168.1.51:8000/'

function App() {
  const [reglas, setReglas] = useState([])
  const [texto_regla, setTextoRegla] = useState("")
  const [resultado_validacion, setResultadoValidacion] = useState(null)
  const [mensajeValidacion, setMensajeValidacion] = useState('')

  const validarRegla = async () => {
    try {
      const textoCodificado = encodeURIComponent(texto_regla)
      const response = await fetch(BASE_URL + `regla_validation?texto_regla=${textoCodificado}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }

      const data = await response.json();
      // Procesamiento específico para la estructura {"validacion": boolean}
      const esValida = data.validacion; // Extraemos el booleano del campo "validacion"
      setResultadoValidacion(esValida);
      
      if (esValida) {
        setMensajeValidacion('✅ La regla es válida');
      } else {
        setMensajeValidacion('❌ La regla no es válida');
      }
      
    } catch (error) {
      console.error('Error al validar la regla:', error);
      setMensajeValidacion('⚠️ Error al conectar con el servidor');
      setResultadoValidacion(null);
    }
  };

  const crearRegla = async () => {
    try {
      const response = await fetch(BASE_URL + 'reglas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ texto_regla: texto_regla }),
      })

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al crear la regla');
      }
      const createdData = await response.json();
    console.log('Regla creada:', createdData);
    window.location.reload()
    
    } catch (error) {
    console.error('Error:', error);
      setMensajeValidacion('⚠️ Error al crear la regla');
      setResultadoValidacion(null);
    }
  }

  const eliminarRegla = async (regla_id) => {
    try {
      const response = await fetch(`${BASE_URL}reglas/?regla_id=${regla_id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Error al eliminar la regla');
      }
      window.location.reload()
      
    } catch (error) {
      console.error('Error al eliminar:', error);
      setMensajeValidacion('⚠️ Error al borrar la regla');
      setResultadoValidacion(null);
    }
  }
  useEffect(() => {
    fetch(BASE_URL + 'reglas')
      .then(response => {
        const json = response.json()
        console.log(json);
        if (response.ok) {
          return json
        }
        throw response
      })
      .then(data => {
        setReglas(data)
      })
      .catch(error => {
        console.log(error);
        alert(error)
      })
  }, [])

  return (
    <div className='App'>
      <div className='reglas_title'>Reglas activas</div>
      <div className='app_reglas'>
        {
          reglas.map((regla, index) => (
            <div key={regla.regla_id} className='regla-item'>
              <div className='regla-texto'>{regla.texto_regla}</div>
              <div className='regla-fecha'>
                {new Date(regla.fecha_creacion).toLocaleDateString()}
              </div>
              <button 
                onClick={() => eliminarRegla(regla.regla_id)}
                className='boton-borrar'
              >
                Borrar
              </button>
            </div>
          ))
        }
        <div className='nueva_regla'>
          <div className='nueva_regla_container'>
            <span className='nueva_regla_label'>Nueva regla:</span>
            <input 
              className='nueva_regla_input' 
              type='text' 
              id="texto_input"
              placeholder='Texto regla' 
              onChange={(event) => setTextoRegla(event.target.value)}
              value={texto_regla} 
            />
            <button className='boton_validar' onClick={validarRegla}>
              Validar regla
            </button>
            <button className='boton_crear' onClick={crearRegla}>
              Crear regla
            </button>
          </div>
          {mensajeValidacion && (
            <div className={`mensaje-validacion ${resultado_validacion ? 'valido' : 'invalido'}`}>
              {mensajeValidacion}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App

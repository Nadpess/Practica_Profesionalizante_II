"""Rutas de la API del sistema experto"""

from fastapi import APIRouter, HTTPException, Body, Header, UploadFile, File, Form
from typing import Optional
import os
import json
import time
import uuid
import threading
from pathlib import Path
from api.auth import validar_usuario, crear_token, validar_token, eliminar_token
from api.base_conocimiento import BaseConocimiento
from api.engine import MotorInferencia
from api.stats import stats_manager
from api.rag.cache import registrar_feedback, stats_cache

router = APIRouter(prefix="/api", tags=["Sistema Experto"])

base = BaseConocimiento()
motor_global = MotorInferencia(base)

# ── Sesiones del SE estático ──────────────────────────────────────────────────
# Cada entrada: key -> {"motor": MotorInferencia, "ts": float}.
# Antes era un dict global sin lock ni expiración: crecía sin límite (leak) y no
# era thread-safe. Ahora se protege con lock y expira por inactividad.
# NOTA: la key sigue siendo "maquina|categoria", así que dos técnicos
# diagnosticando la MISMA máquina+categoría a la vez todavía comparten motor.
# La aislación por usuario real requiere un session_id enviado por el frontend
# (pendiente, se integrará con el refactor de UX).
sesiones = {}
_sesiones_lock = threading.Lock()
SESION_SE_TTL = 1800  # 30 minutos de inactividad


def _guardar_sesion(key: str, motor: "MotorInferencia"):
    ahora = time.time()
    with _sesiones_lock:
        sesiones[key] = {"motor": motor, "ts": ahora}
        # Limpieza oportunista de sesiones expiradas
        expiradas = [k for k, v in sesiones.items() if ahora - v["ts"] > SESION_SE_TTL]
        for k in expiradas:
            del sesiones[k]


def _obtener_sesion(key: str):
    with _sesiones_lock:
        entry = sesiones.get(key)
        if not entry:
            return None
        if time.time() - entry["ts"] > SESION_SE_TTL:
            del sesiones[key]
            return None
        entry["ts"] = time.time()
        return entry["motor"]

# Mapeo fijo de nombres de manuales a claves de base de conocimiento
MAPEO_NOMBRES_FIJO = {
    "Generador Generac Guardian": "generador_generac",
    "Hidrolavadora Kärcher": "hidrolavadora_karcher",
    "Motor Cummins": "motor_cummins",
    "Soldadora Miller Ranger 305D": "soldadora_miller_ranger"
}

def normalizar_nombre_para_clave(nombre: str) -> str:
    """Convierte un nombre de máquina a formato de clave (ej: 'Motor Diesel' -> 'motor_diesel')"""
    # Primero verificar si hay un mapeo fijo
    if nombre in MAPEO_NOMBRES_FIJO:
        return MAPEO_NOMBRES_FIJO[nombre]
    # Si no, normalizar el nombre
    return nombre.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n').replace('ä', 'a').replace('ö', 'o').replace('ü', 'u')

# Cargar nombres de máquinas dinámicamente desde la base de conocimiento
def cargar_nombres_maquinas():
    """Carga los nombres de máquinas desde la base de conocimiento y manuales"""
    nombres_maquinas = {}
    try:
        # Primero cargar desde manuales (tienen los nombres correctos)
        manuales_path = Path(__file__).parent.parent / "data" / "manuales.json"
        if manuales_path.exists():
            with open(manuales_path, 'r', encoding='utf-8') as f:
                manuales = json.load(f)
                for manual in manuales:
                    nombre = manual["nombre"]
                    clave = normalizar_nombre_para_clave(nombre)
                    nombres_maquinas[nombre] = clave
        
        # Luego cargar desde base de conocimiento para máquinas sin manual
        base_conocimiento_path = Path(__file__).parent.parent / "data" / "base_conocimiento.json"
        if base_conocimiento_path.exists():
            with open(base_conocimiento_path, 'r', encoding='utf-8') as f:
                base_conocimiento = json.load(f)
                for clave_maquina in base_conocimiento.keys():
                    # Solo agregar si no existe ya (prioridad a manuales.json)
                    if clave_maquina not in nombres_maquinas.values():
                        # Convertir clave a nombre amigable
                        nombre_amigable = clave_maquina.replace('_', ' ').title()
                        nombres_maquinas[nombre_amigable] = clave_maquina
    except Exception as e:
        print(f"Error al cargar nombres de máquinas: {str(e)}")
    
    return nombres_maquinas

NOMBRES_MAQUINAS = cargar_nombres_maquinas()
NOMBRES_AMIGABLES = {v: k for k, v in NOMBRES_MAQUINAS.items()}

def normalizar_nombre_maquina(nombre: str) -> str:
    return NOMBRES_MAQUINAS.get(nombre, nombre)

@router.get("/")
def home():
    """Ruta base de la API."""
    return {"mensaje": "API del Sistema Experto activa"}


@router.post("/login")
def login(username: str = Body(...), password: str = Body(...)):
    if validar_usuario(username, password):
        return {"success": True, "message": "Login correcto"}
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")


@router.post("/admin/login")
def admin_login(username: str = Body(...), password: str = Body(...)):
    """Login que retorna un token de sesión y el rol del usuario."""
    usuario = validar_usuario(username, password)
    if usuario:
        token = crear_token(usuario["username"], usuario["role"])
        return {
            "success": True, 
            "token": token, 
            "username": usuario["username"],
            "role": usuario["role"]
        }
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")


@router.get("/admin/verify")
def admin_verify(authorization: Optional[str] = Header(None, alias="Authorization")):
    """Verifica si el token actual sigue siendo válido. Usado al cargar la página."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    token = authorization.replace("Bearer ", "")
    user_data = validar_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return {"valid": True, "username": user_data["username"], "role": user_data["role"]}


@router.post("/admin/logout")
def admin_logout(authorization: Optional[str] = Header(None, alias="Authorization")):
    """Cierra sesión del administrador."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    
    token = authorization.replace("Bearer ", "")
    eliminar_token(token)
    return {"success": True, "message": "Sesión cerrada correctamente"}


@router.get("/admin/stats")
def obtener_estadisticas(authorization: Optional[str] = Header(None, alias="Authorization")):
    """Retorna las estadísticas del sistema (requiere autenticación de admin)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autorizado")
    
    token = authorization.replace("Bearer ", "")
    user_data = validar_token(token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    # Verificar que sea admin
    if user_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo administradores.")
    
    estadisticas = stats_manager.obtener_estadisticas()
    return estadisticas


@router.get("/maquinas")
def listar_maquinas():
    """Lista todas las máquinas disponibles, ordenadas por popularidad (consultas totales)."""
    nombres_amigables = {
        "hidrolavadora_karcher": "Hidrolavadora Kärcher",
        "generador_generac": "Generador Generac Guardian",
        "motor_cummins": "Motor Cummins",
        "soldadora_miller_ranger": "Soldadora Miller Ranger 305D"
    }

    maquinas_tecnicas = base.listar_maquinas()
    estadisticas = stats_manager.obtener_estadisticas()
    rag_counts   = estadisticas.get("consultas_rag_por_maquina", {})
    se_counts    = estadisticas.get("diagnosticos_por_maquina", {})

    resultado = []
    for m in maquinas_tecnicas:
        nombre = nombres_amigables.get(m, m)
        # Suma consultas RAG + diagnósticos SE (buscando por nombre técnico y amigable)
        total = (rag_counts.get(nombre, 0) + rag_counts.get(m, 0)
               + se_counts.get(nombre, 0)  + se_counts.get(m, 0))
        resultado.append({"nombre": nombre, "consultas": total})

    # Ordenar por popularidad descendente
    resultado.sort(key=lambda x: x["consultas"], reverse=True)
    return {"maquinas": [r["nombre"] for r in resultado], "stats": resultado}


@router.get("/categorias/{nombre_maquina}")
def listar_categorias(nombre_maquina: str):
    """Devuelve las categorías disponibles para una máquina específica."""
    nombre_tecnico = normalizar_nombre_maquina(nombre_maquina)
    categorias = base.listar_categorias(nombre_tecnico)
    return {"categorias": categorias}


@router.post("/diagnosticar/iniciar/{nombre_maquina}/{categoria}")
def iniciar_diagnostico(nombre_maquina: str, categoria: str):
    """
    Inicia el diagnóstico de una máquina específica para la categoría seleccionada.
    Devuelve la primera pregunta u opciones para el frontend.
    """
    try:
        # Normalizar nombre de máquina
        nombre_tecnico = normalizar_nombre_maquina(nombre_maquina)
        
        motor = MotorInferencia(base)
        
        # Paso 1: Iniciar el motor (carga categorías de la máquina)
        motor.iniciar_diagnostico(nombre_tecnico) 
        
        # Paso 2: Seleccionar la categoría (obtiene la 1ra pregunta o resultado)
        # !! ESTE ES EL PASO CRÍTICO QUE FALTABA !!
        resultado = motor.seleccionar_categoria(categoria) 

        # Sesión aislada por usuario: una key única por cada inicio de diagnóstico.
        # Antes la key era "maquina|categoria", compartida entre todos los técnicos.
        session_id = uuid.uuid4().hex
        _guardar_sesion(session_id, motor)

        # Registrar estadística (usar nombre técnico)
        stats_manager.registrar_diagnostico_iniciado(nombre_tecnico, categoria)

        # Si el diagnóstico llegó directamente a una falla (resultado final), 
        # marcarlo como completado inmediatamente
        if "falla" in resultado and "soluciones" in resultado:
            stats_manager.registrar_diagnostico_completado(nombre_tecnico, categoria, resultado["falla"])

        # Retornamos el resultado del Paso 2 con el session_id para que el
        # frontend lo reenvíe en cada /avanzar.
        if isinstance(resultado, dict):
            resultado["session_id"] = session_id
        return resultado

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/diagnosticar/avanzar/{nombre_maquina}/{categoria}")
def avanzar_diagnostico(nombre_maquina: str, categoria: str, respuesta: str = Body(..., embed=True), session_id: Optional[str] = Body(None, embed=True)):
    """
    Avanza un paso en el árbol de diagnóstico según la respuesta del usuario.
    Devuelve la siguiente pregunta u opciones, o la falla y soluciones si se llegó a un nodo hoja.
    """
    # Normalizar nombre de máquina
    nombre_tecnico = normalizar_nombre_maquina(nombre_maquina)
    
    # Preferir el session_id del frontend (aislado por usuario); si no llega,
    # usar la key vieja como fallback compatible.
    key = session_id or f"{nombre_tecnico}|{categoria}"
    motor = _obtener_sesion(key)

    if motor is None:
        raise HTTPException(status_code=404, detail="No se encontró una sesión activa para esta máquina y categoría.")

    resultado = motor.avanzar(respuesta)
    
    # Si el diagnóstico llegó a una falla (resultado final), registrar como completado
    if "falla" in resultado and "soluciones" in resultado:
        stats_manager.registrar_diagnostico_completado(nombre_tecnico, categoria, resultado["falla"])
    
    return resultado


# ========== GESTIÓN DE MANUALES ==========

MANUALES_DIR = Path(__file__).parent.parent / "data" / "manuales_pdf"
MANUALES_JSON = Path(__file__).parent.parent / "data" / "manuales.json"
BASE_CONOCIMIENTO_JSON = Path(__file__).parent.parent / "data" / "base_conocimiento.json"

# Crear directorio si no existe
MANUALES_DIR.mkdir(parents=True, exist_ok=True)

# Crear archivo JSON si no existe
if not MANUALES_JSON.exists():
    with open(MANUALES_JSON, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def generar_plantilla_base_conocimiento(nombre_maquina: str, nombre_archivo: str) -> dict:
    """Genera una plantilla de base de conocimiento para una nueva máquina"""
    return {
        "categorias": [
            {
                "categoria": "Problemas Eléctricos",
                "ramas": [
                    {
                        "pregunta": "¿La máquina enciende?",
                        "ramas": [
                            {
                                "atributo": "No enciende",
                                "falla": "Falta de alimentación eléctrica",
                                "referencia": nombre_archivo,
                                "soluciones": [
                                    "Verificar la conexión a la red eléctrica",
                                    "Revisar el cable de alimentación",
                                    "Comprobar el interruptor principal",
                                    "Verificar fusibles o disyuntores"
                                ]
                            },
                            {
                                "atributo": "Enciende pero se apaga",
                                "falla": "Protección térmica activada o cortocircuito",
                                "referencia": nombre_archivo,
                                "soluciones": [
                                    "Dejar enfriar la máquina",
                                    "Verificar ventilación adecuada",
                                    "Revisar posibles cortocircuitos",
                                    "Consultar el manual técnico"
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "categoria": "Problemas Mecánicos",
                "ramas": [
                    {
                        "pregunta": "¿Hay ruidos anormales?",
                        "ramas": [
                            {
                                "atributo": "Ruido excesivo o vibración",
                                "falla": "Desgaste de componentes mecánicos",
                                "referencia": nombre_archivo,
                                "soluciones": [
                                    "Verificar el estado de rodamientos",
                                    "Revisar alineación de componentes",
                                    "Comprobar el nivel de lubricación",
                                    "Inspeccionar partes móviles"
                                ]
                            },
                            {
                                "atributo": "No hay ruidos anormales",
                                "falla": "Bloqueo o atasco mecánico",
                                "referencia": nombre_archivo,
                                "soluciones": [
                                    "Verificar que no haya obstrucciones",
                                    "Revisar el sistema de transmisión",
                                    "Comprobar el estado de correas o cadenas"
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "categoria": "Problemas de Rendimiento",
                "ramas": [
                    {
                        "pregunta": "¿La máquina funciona con potencia reducida?",
                        "ramas": [
                            {
                                "atributo": "Sí, baja potencia",
                                "falla": "Desgaste o falta de mantenimiento",
                                "referencia": nombre_archivo,
                                "soluciones": [
                                    "Realizar mantenimiento preventivo",
                                    "Verificar filtros y limpiar si es necesario",
                                    "Revisar el estado de componentes principales",
                                    "Consultar el manual de mantenimiento"
                                ]
                            },
                            {
                                "atributo": "No, funciona normal",
                                "falla": "Posible problema de configuración",
                                "referencia": nombre_archivo,
                                "soluciones": [
                                    "Verificar configuración de parámetros",
                                    "Revisar el manual de usuario",
                                    "Contactar con soporte técnico"
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "categoria": "Otros Problemas",
                "ramas": [
                    {
                        "falla": "Problema no identificado",
                        "referencia": nombre_archivo,
                        "soluciones": [
                            "Consultar el manual técnico completo",
                            "Contactar con el servicio técnico autorizado",
                            "Verificar garantía del equipo"
                        ]
                    }
                ]
            }
        ]
    }


def agregar_maquina_base_conocimiento(nombre_maquina: str, nombre_archivo: str):
    """Agrega una nueva máquina a la base de conocimiento"""
    try:
        # Leer base de conocimiento actual
        with open(BASE_CONOCIMIENTO_JSON, 'r', encoding='utf-8') as f:
            base_conocimiento = json.load(f)
        
        # Generar clave normalizada
        clave_maquina = normalizar_nombre_para_clave(nombre_maquina)

        # Sin plantilla genérica: categorías vacías → el frontend usará SE Dinámico (RAG)
        base_conocimiento[clave_maquina] = {"categorias": []}
        
        # Guardar base de conocimiento actualizada
        with open(BASE_CONOCIMIENTO_JSON, 'w', encoding='utf-8') as f:
            json.dump(base_conocimiento, f, ensure_ascii=False, indent=2)
        
        # Actualizar mapeo de nombres
        NOMBRES_MAQUINAS[nombre_maquina] = clave_maquina
        NOMBRES_AMIGABLES[clave_maquina] = nombre_maquina
        
        # Recargar base de conocimiento en el motor
        global base, motor_global
        base = BaseConocimiento()
        motor_global = MotorInferencia(base)
        
        return True
    except Exception as e:
        print(f"Error al agregar máquina a base de conocimiento: {str(e)}")
        return False


def eliminar_maquina_base_conocimiento(nombre_maquina: str):
    """Elimina una máquina de la base de conocimiento"""
    try:
        # Leer base de conocimiento actual
        with open(BASE_CONOCIMIENTO_JSON, 'r', encoding='utf-8') as f:
            base_conocimiento = json.load(f)
        
        # Generar clave normalizada
        clave_maquina = normalizar_nombre_para_clave(nombre_maquina)
        
        # Eliminar de la base de conocimiento si existe
        if clave_maquina in base_conocimiento:
            del base_conocimiento[clave_maquina]
            
            # Guardar base de conocimiento actualizada
            with open(BASE_CONOCIMIENTO_JSON, 'w', encoding='utf-8') as f:
                json.dump(base_conocimiento, f, ensure_ascii=False, indent=2)
            
            # Actualizar mapeo de nombres
            if nombre_maquina in NOMBRES_MAQUINAS:
                del NOMBRES_MAQUINAS[nombre_maquina]
            if clave_maquina in NOMBRES_AMIGABLES:
                del NOMBRES_AMIGABLES[clave_maquina]
            
            # Recargar base de conocimiento en el motor
            global base, motor_global
            base = BaseConocimiento()
            motor_global = MotorInferencia(base)
        
        return True
    except Exception as e:
        print(f"Error al eliminar máquina de base de conocimiento: {str(e)}")
        return False


@router.get("/admin/manuales")
def listar_manuales(authorization: Optional[str] = Header(None, alias="Authorization")):
    """Obtener lista de manuales disponibles."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    
    token = authorization.replace("Bearer ", "")
    usuario = validar_token(token)
    
    if not usuario or usuario.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo administradores.")
    
    try:
        with open(MANUALES_JSON, 'r', encoding='utf-8') as f:
            manuales = json.load(f)
        return {"manuales": manuales}
    except Exception as e:
        return {"manuales": []}


@router.post("/admin/manuales/upload")
async def subir_manual(
    nombreManual: str = Form(...),
    archivo: UploadFile = File(...),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Subir un nuevo manual PDF."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    
    token = authorization.replace("Bearer ", "")
    usuario = validar_token(token)
    
    if not usuario or usuario.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo administradores.")
    
    # Validar que sea un PDF
    if not archivo.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
    
    try:
        # Generar nombre de archivo seguro
        nombre_archivo = f"{nombreManual.replace(' ', '_')}.pdf"
        ruta_archivo = MANUALES_DIR / nombre_archivo
        
        # Guardar el archivo
        contenido = await archivo.read()
        with open(ruta_archivo, 'wb') as f:
            f.write(contenido)
        
        # Actualizar el JSON de manuales
        with open(MANUALES_JSON, 'r', encoding='utf-8') as f:
            manuales = json.load(f)
        
        # Agregar nuevo manual si no existe
        nuevo_manual = {
            "nombre": nombreManual,
            "archivo": nombre_archivo,
            "fecha_subida": str(Path(ruta_archivo).stat().st_mtime)
        }
        
        # Verificar si ya existe y actualizar
        existe = False
        for i, manual in enumerate(manuales):
            if manual["nombre"] == nombreManual:
                manuales[i] = nuevo_manual
                existe = True
                break
        
        if not existe:
            manuales.append(nuevo_manual)
        
        # Guardar JSON actualizado
        with open(MANUALES_JSON, 'w', encoding='utf-8') as f:
            json.dump(manuales, f, ensure_ascii=False, indent=2)
        
        # Agregar máquina a la base de conocimiento automáticamente
        if not existe:  # Solo si es una máquina nueva
            agregar_maquina_base_conocimiento(nombreManual, nombre_archivo)
        
        return {
            "success": True,
            "message": f"Manual '{nombreManual}' subido correctamente y agregado a la base de conocimiento",
            "manual": nuevo_manual
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir el manual: {str(e)}")


@router.delete("/admin/manuales/{nombre_archivo}")
def eliminar_manual(
    nombre_archivo: str,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Eliminar un manual."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    
    token = authorization.replace("Bearer ", "")
    usuario = validar_token(token)
    
    if not usuario or usuario.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo administradores.")
    
    try:
        # Obtener el nombre de la máquina antes de eliminar
        with open(MANUALES_JSON, 'r', encoding='utf-8') as f:
            manuales = json.load(f)
        
        nombre_maquina = None
        for manual in manuales:
            if manual["archivo"] == nombre_archivo:
                nombre_maquina = manual["nombre"]
                break
        
        # Eliminar archivo físico
        ruta_archivo = MANUALES_DIR / nombre_archivo
        if ruta_archivo.exists():
            ruta_archivo.unlink()
        
        # Actualizar JSON
        manuales = [m for m in manuales if m["archivo"] != nombre_archivo]
        
        with open(MANUALES_JSON, 'w', encoding='utf-8') as f:
            json.dump(manuales, f, ensure_ascii=False, indent=2)
        
        # Eliminar de la base de conocimiento
        if nombre_maquina:
            eliminar_maquina_base_conocimiento(nombre_maquina)
        
        return {"success": True, "message": "Manual eliminado correctamente y removido de la base de conocimiento"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el manual: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
#  FEEDBACK — validación explícita de respuestas RAG
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/feedback")
def registrar_feedback_usuario(
    payload: dict = Body(...),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Registra el feedback 👍/👎 de un técnico sobre una respuesta RAG.
    Guarda/refuerza en cache si es positivo, penaliza si es negativo.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autorizado")
    token = authorization.replace("Bearer ", "")
    if not validar_token(token):
        raise HTTPException(status_code=401, detail="Token inválido")

    maquina   = payload.get("maquina", "")
    pregunta  = payload.get("pregunta", "")
    respuesta = payload.get("respuesta", "")
    positivo  = bool(payload.get("positivo", True))
    confianza = int(payload.get("confianza", 75))
    paginas   = payload.get("paginas", [])
    secciones = payload.get("secciones", [])

    if not maquina or not pregunta:
        raise HTTPException(status_code=400, detail="Faltan campos obligatorios")

    ok = registrar_feedback(
        nombre_maquina=maquina,
        pregunta=pregunta,
        positivo=positivo,
        respuesta=respuesta,
        confianza=confianza,
        paginas=paginas,
        secciones=secciones,
    )
    return {"success": ok, "tipo": "positivo" if positivo else "negativo"}


# NOTA: El SE Dinámico (endpoints /se-dinamico/*) fue eliminado (2026-05-28).
# Los manuales sin árbol de conocimiento ahora se atienden por consulta libre RAG.
# El módulo api/rag/se_dinamico.py quedó sin uso y puede borrarse.

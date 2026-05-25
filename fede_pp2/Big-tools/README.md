# 🔧 Big Tools — Sistema Experto de Diagnóstico de Máquinas

<div align="center">

**Un sistema inteligente para diagnosticar fallas en maquinaria industrial**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![FastAPI](https://img.shields.io/badge/fastapi-0.104+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

[🚀 Inicio Rápido](#-inicio-rápido) • [📖 Documentación](#-documentación-completa) • [🏗️ Estructura](#-estructura-del-proyecto) • [🔌 API](#-api-endpoints) • [🎯 Mejoras Futuras](#-mejoras-futuras)

</div>

---

## 📘 Documentación completa 

**Disponible en:** https://axumis.github.io/Big-Tools/

---

## 📋 Descripción General

**Big Tools** es una aplicación web completa que ayuda a técnicos y administradores a diagnosticar fallas en máquinas industriales mediante:

- 🤖 **Chatbot Inteligente:** Guía interactiva que usa un árbol de decisión para diagnósticos precisos
- 📊 **Dashboard Administrativo:** Panel de control con estadísticas, gestión de manuales y exportación de reportes
- ⚙️ **Motor de Inferencia:** Sistema experto basado en reglas que recorre la base de conocimiento
- 📄 **Gestión Automática de Manuales:** Subida de PDFs con generación automática de base de conocimiento
- 📈 **Estadísticas en Tiempo Real:** Seguimiento de diagnósticos, fallas comunes y tendencias

### ✨ Características Principales

- ✅ Diagnóstico interactivo paso a paso
- ✅ Sistema de roles (Administrador y Técnico)
- ✅ Gestión automática de manuales PDF
- ✅ Generación automática de base de conocimiento
- ✅ Dashboard con gráficos estadísticos (Chart.js)
- ✅ Exportación de reportes en PDF (jsPDF)
- ✅ Interfaz moderna con efectos visuales (Particles.js)
- ✅ Autenticación con tokens de sesión
- ✅ API REST completamente funcional

---

## 🚀 Inicio Rápido

### Requisitos Previos

- **Python 3.8+** (Windows, Linux o macOS)
- **pip** (instalador de paquetes)
- Navegador web moderno

### Instalación (2 minutos)

#### Opción 1: Usuario Windows (Recomendado)

1. Descarga o clona el repositorio:
```powershell
https://github.com/Axumis/Big-Tools
```
2. Haz **doble clic** en `INICIAR_BIG_TOOLS.bat`
3. El sistema automáticamente:
   - ✅ Verifica Python
   - ✅ Instala dependencias
   - ✅ Arranca el backend (FastAPI)
   - ✅ Abre el navegador en `http://127.0.0.1:8000`

#### Opción 2: Desarrollador (Manual)

```powershell
# 1. Crear y activar entorno virtual (recomendado)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Instalar dependencias
python -m pip install -r requirements.txt

# 3. Iniciar backend
cd Backend
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000

# 4. Abrir navegador
http://127.0.0.1:8000

# 5. En otra terminal (con venv activado), generar documentación:
mkdocs serve -a 127.0.0.1:8001 # Accede a http://127.0.0.1:8001/docs

```

#### Opción 3: Linux / macOS

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar backend
cd Backend
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000

# 3. Abrir navegador (el script también lo hace automáticamente)
http://127.0.0.1:8000
```

O ejecuta directamente:

```bash
python run_simple.py
# o
bash run.sh
```

---

## 🔑 Credenciales por Defecto

| Rol | Usuario | Contraseña | Acceso |
|-----|---------|-----------|--------|
| **Administrador** | `admin` | `1234` | Chatbot + Dashboard |
| **Técnico** | `tecnico` | `1234` | Solo Chatbot |

> ⚠️ **Nota:** Cambiar credenciales en producción. Ver `Backend/data/users.json`

---

## 🏗️ Estructura del Proyecto

```
Big-tools/
│
├── 📁 .github/                          # Configuración GitHub
│   ├── 📁 workflows/
│   │   └── ci.yml                       # CI/CD con MkDocs deployment
│
├── 📁 Backend/                          # API FastAPI y lógica del sistema
│   ├── app.py                           # Aplicación principal (servidor)
│   ├── 📁 api/                          # Módulos de la API
│   │   ├── auth.py                      # Autenticación y gestión de tokens
│   │   ├── base_conocimiento.py         # Carga/gestión de base de conocimiento
│   │   ├── engine.py                    # Motor de inferencia (diagnóstico)
│   │   ├── nodo.py                      # Estructura de árbol de decisión
│   │   ├── routes.py                    # Endpoints de la API
│   │   ├── stats.py                     # Gestión de estadísticas
│   │   └──  response.py                  # Modelos de respuesta
│   │
│   ├── 📁 data/                         # Almacenamiento de datos (JSON)
│   │   ├── base_conocimiento.json       # Árbol de decisión para diagnósticos
│   │   ├── users.json                   # Usuarios registrados (SHA256)
│   │   ├── manuales.json                # Índice de manuales PDF
│   │   ├── stats.json                   # Estadísticas de uso
│   │   └── 📁 manuales_pdf/             # Archivos PDF almacenados
│   │       ├── HIDROLAVADORA.pdf
│   │       ├── MANUAL CUMMINS 2.pdf
│   │       ├── ranger_305d.pdf
│   │       └── Generac_Manual_Usuario_Guardian_Series (1).pdf 
│   │ 
├── 📁 docs/                             # Sitio documentación MkDocs
│   │   └── 📁 assets/                   # Archivos PDF almacenados
│   │       ├── logo.ico                 # Imagen para la pestaña del navegador
│   │       └── logo.png                 # Imagen para la página en MKDocs
│   │
│   ├── index.md                         # Página de inicio documentación
│   └── INFORME_SISTEMA_EXPERTO.md       # Informe técnico completo
│
├── 📁 Frontend/                         # Interfaz web (HTML/CSS/JS)
│   ├── index.html                       # Página de login y chatbot
│   ├── admin.html                       # Dashboard administrativo
│   │
│   ├── 📁 js/                           # JavaScript (lógica del cliente)
│   │   ├── main.js                      # Lógica del chatbot
│   │   ├── admin.js                     # Lógica del dashboard
│   │   └── config.js                    # Configuración (detección URL API)
│   │
│   ├── 📁 css/                          # Estilos CSS
│   │   ├── style.css                    # Estilos del chatbot
│   │   └── admin.css                    # Estilos del dashboard
│   │
│   └── 📁 assets/                       # Recursos multimedia
│       ├── 📁 img/
│       │   ├── hidrolavadora.jpg
│       │   ├── generador.jpg
│       │   ├── motor.jpg
│       │   ├── soldadora.jpg
│       │   └── INSTRUCCIONES_IMAGENES.TXT
│       
├── 📄 COMO_USAR.txt                     # Guía de uso rápido
├── 📄 README.md                         # Este archivo
│
├── 📋 requirements.txt                  # Dependencias Python
├── 📋 mkdocs.yml                        # Documentación en MKDocs
│
├── INICIAR_BIG_TOOLS.bat                # ⭐ Recomendado para Windows
├── run.bat                              # Alternativa para Windows
├── run.sh                               # Para Linux/macOS
├──  run_simple.py                        # Script Python multiplataforma
│
├── .gitignore                           # Archivos ignorados por git
│   └── 📁 venv/                         # Entorno virtual Python
│
└── 📁 .git/                             # Repositorio Git
```

---

## 🔌 API Endpoints

Base URL: `http://127.0.0.1:8000/api`

### Endpoints Públicos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/maquinas` | Lista todas las máquinas disponibles |
| `GET` | `/categorias/{nombre_maquina}` | Categorías de problemas para una máquina |
| `POST` | `/admin/login` | Autenticación (devuelve token) |
| `POST` | `/admin/logout` | Cerrar sesión |

### Endpoints de Diagnóstico

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/diagnosticar/iniciar/{maquina}/{categoria}` | Inicia diagnóstico (devuelve primera pregunta) |
| `POST` | `/diagnosticar/avanzar/{maquina}/{categoria}` | Avanza en el árbol de decisión |

### Endpoints Administrativos (Requieren Token)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/admin/stats` | Estadísticas de uso (solo admin) |
| `GET` | `/admin/manuales` | Lista de manuales (solo admin) |
| `POST` | `/admin/manuales/upload` | Subir nuevo manual PDF (solo admin) |
| `DELETE` | `/admin/manuales/{archivo}` | Eliminar manual (solo admin) |

### Rutas Estáticas

| Ruta | Contenido |
|------|----------|
| `/` | Página de login / chatbot |
| `/admin` | Dashboard administrativo |
| `/manuales/{archivo}` | Acceso a PDFs de manuales |

---

## 📊 Ejemplos de Uso (PowerShell)

### 1️⃣ Obtener Lista de Máquinas

```powershell
curl -s "http://127.0.0.1:8000/api/maquinas" | ConvertFrom-Json

# Respuesta:
# {
#   "maquinas": [
#     "Hidrolavadora Kärcher",
#     "Generador Generac Guardian",
#     "Motor Cummins",
#     "Soldadora Miller Ranger 305D"
#   ]
# }
```

### 2️⃣ Login de Administrador

```powershell
$body = @{
    username = "admin"
    password = "1234"
} | ConvertTo-Json

curl -s -X POST "http://127.0.0.1:8000/api/admin/login" `
  -H "Content-Type: application/json" `
  -d $body | ConvertFrom-Json

# Respuesta:
# {
#   "token": "abc123def456...",
#   "rol": "admin",
#   "mensaje": "Login exitoso"
# }
```

### 3️⃣ Obtener Categorías de una Máquina

```powershell
$maquina = [uri]::EscapeDataString("Hidrolavadora Kärcher")

curl -s "http://127.0.0.1:8000/api/categorias/$maquina" | ConvertFrom-Json

# Respuesta:
# {
#   "categorias": [
#     "El aparato no funciona",
#     "Problemas de presión",
#     "Problemas de caudal",
#     "Problemas eléctricos"
#   ]
# }
```

### 4️⃣ Iniciar Diagnóstico

```powershell
$maquina = [uri]::EscapeDataString("Hidrolavadora Kärcher")
$categoria = [uri]::EscapeDataString("El aparato no funciona")

curl -s -X POST "http://127.0.0.1:8000/api/diagnosticar/iniciar/$maquina/$categoria" | ConvertFrom-Json

# Respuesta:
# {
#   "pregunta": "¿Hay tensión en la toma de corriente?",
#   "opciones": ["Sí", "No", "No sé"],
#   "id_diagnostico": "diag_12345"
# }
```

### 5️⃣ Avanzar en el Diagnóstico

```powershell
$maquina = [uri]::EscapeDataString("Hidrolavadora Kärcher")
$categoria = [uri]::EscapeDataString("El aparato no funciona")
$body = @{
    respuesta = "No"
} | ConvertTo-Json

curl -s -X POST "http://127.0.0.1:8000/api/diagnosticar/avanzar/$maquina/$categoria" `
  -H "Content-Type: application/json" `
  -d $body | ConvertFrom-Json

# Respuesta puede ser:
# {
#   "falla": "Sin tensión de entrada",
#   "soluciones": [
#     "Verificar la conexión a la red eléctrica",
#     "Revisar el cable de alimentación",
#     "Comprobar el interruptor principal"
#   ],
#   "referencia": "HIDROLAVADORA.pdf"
# }
```

### 6️⃣ Subir Nuevo Manual (Admin)

```powershell
$token = "<tu_token_aqui>"

curl -X POST "http://127.0.0.1:8000/api/admin/manuales/upload" `
  -H "Authorization: Bearer $token" `
  -F "nombreManual=Compresor Atlas Copco" `
  -F "archivo=@C:\ruta\al\manual.pdf"

# Respuesta:
# {
#   "mensaje": "Manual subido exitosamente",
#   "nombreManual": "Compresor Atlas Copco",
#   "archivo": "compresor_atlas_copco.pdf"
# }
```

### 7️⃣ Obtener Estadísticas (Admin)

```powershell
$token = "<tu_token_aqui>"

curl -s -H "Authorization: Bearer $token" `
  "http://127.0.0.1:8000/api/admin/stats" | ConvertFrom-Json

# Respuesta:
# {
#   "total_diagnosticos": 245,
#   "diagnosticos_por_maquina": {...},
#   "fallas_comunes": [...],
#   "diagnosticos_por_tecnico": {...}
# }
```

---

## 📁 Formato de Datos

### Base de Conocimiento (`Backend/data/base_conocimiento.json`)

Estructura del árbol de decisión para diagnósticos:

```json
{
  "hidrolavadora_karcher": {
    "categorias": [
      {
        "categoria": "El aparato no funciona",
        "ramas": [
          {
            "pregunta": "¿Hay tensión en la toma de corriente?",
            "ramas": [
              {
                "atributo": "No",
                "falla": "Sin tensión de entrada",
                "referencia": "HIDROLAVADORA.pdf",
                "soluciones": [
                  "Verificar la conexión a la red eléctrica",
                  "Revisar el cable de alimentación",
                  "Comprobar el interruptor principal",
                  "Verificar fusibles o disyuntores"
                ]
              },
              {
                "atributo": "Sí",
                "pregunta": "¿Se enciende el piloto de control?",
                "ramas": [
                  {
                    "atributo": "No",
                    "falla": "Falla en el circuito de control",
                    "referencia": "HIDROLAVADORA.pdf",
                    "soluciones": [...]
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### Usuarios (`Backend/data/users.json`)

```json
{
  "admin": {
    "password": "81dc9bdb52d04dc20036dbd8313ed055",
    "rol": "admin"
  },
  "tecnico": {
    "password": "81dc9bdb52d04dc20036dbd8313ed055",
    "rol": "tecnico"
  }
}
```

> 🔐 **Nota:** Las contraseñas se almacenan como hash SHA256

### Manuales (`Backend/data/manuales.json`)

```json
{
  "hidrolavadora_karcher": {
    "nombre": "Hidrolavadora Kärcher",
    "archivo": "HIDROLAVADORA.pdf",
    "fecha_subida": "2025-11-01T10:30:00",
    "url": "/manuales/HIDROLAVADORA.pdf"
  }
}
```

### Estadísticas (`Backend/data/stats.json`)

```json
{
  "diagnosticos_totales": 245,
  "diagnosticos_por_maquina": {
    "hidrolavadora_karcher": 120,
    "generador_generac": 80,
    "motor_cummins": 45
  },
  "fallas_mas_comunes": [
    {"falla": "Sin tensión", "count": 45},
    {"falla": "Filtro obstruido", "count": 38}
  ]
}
```

---

## 🔐 Seguridad y Configuración

### Autenticación

- ✅ Tokens de sesión con tiempo de expiración
- ✅ Contraseñas hasheadas con SHA256
- ✅ Sistema de roles (admin/tecnico)
- ⚠️ **Producción:** Usar bcrypt/scrypt en lugar de SHA256

### CORS

```python
# Backend/app.py
allow_origins=["*"]  # Desarrollo: permisivo
# Producción: especificar orígenes concretos
```

### Recomendaciones para Producción

1. **Cambiar credenciales** por defecto en `Backend/data/users.json`
2. **Habilitar HTTPS** (usar certificados SSL)
3. **Migrar a bcrypt/scrypt** para hashing de contraseñas
4. **Usar Redis** o base de datos para tokens (en lugar de memoria)
5. **Restringir CORS** a dominios específicos
6. **Configurar backups** automáticos de datos
7. **Usar variables de entorno** para configuración sensible
8. **Habilitar logging** y monitoreo

---

## 🛠️ Desarrollo

### Estructura Backend

**Backend/app.py** - Aplicación FastAPI principal:
- Monta estáticos (Frontend)
- Configura CORS
- Registra rutas API

**Backend/api/routes.py** - Endpoints de la API:
- Login/logout
- Listado de máquinas y categorías
- Diagnóstico (iniciar/avanzar)
- Admin (stats, manuales)

**Backend/api/engine.py** - Motor de inferencia:
- `MotorInferencia.iniciar_diagnostico()` - Inicia árbol
- `MotorInferencia.avanzar()` - Navega el árbol
- `MotorInferencia._pregunta_actual()` - Obtiene pregunta
- `MotorInferencia._resultado_final()` - Obtiene resultado

**Backend/api/base_conocimiento.py** - Gestión de datos:
- Carga JSON
- Valida estructura
- Proporciona métodos de acceso

**Backend/api/auth.py** - Autenticación:
- `validar_usuario()` - Verifica credenciales
- `crear_token()` - Genera token
- `validar_token()` - Verifica token
- `eliminar_token()` - Cierra sesión

### Estructura Frontend

**Frontend/js/main.js** - Lógica del chatbot:
- Autenticación
- Flujo de diagnóstico
- Exportación a PDF

**Frontend/js/admin.js** - Lógica del dashboard:
- Gráficos (Chart.js)
- Gestión de manuales
- Estadísticas

**Frontend/js/config.js** - Configuración:
- Detecta URL del servidor
- Expone `window.API_URL`

---

## 📈 Uso del Sistema

### Flujo para Técnico

1. **Login** → Ingresa credenciales
2. **Seleccionar Máquina** → Elige de la lista
3. **Seleccionar Categoría** → Tipo de problema
4. **Responder Preguntas** → El chatbot pregunta
5. **Obtener Diagnóstico** → Falla + soluciones
6. **Exportar PDF** → Generar reporte

### Flujo para Administrador

1. **Login** → Ingresa credenciales
2. **Dashboard** → Ver estadísticas
3. **Gestionar Manuales** → Subir/eliminar PDFs
4. **Ver Reportes** → Diagnosticos por máquina/técnico
5. **Exportar** → PDF o CSV con datos

---

## 📊 Máquinas Disponibles

El sistema viene con estas máquinas configuradas:

| Máquina | Archivo Manual | Categorías |
|---------|----------------|-----------|
| **Hidrolavadora Kärcher** | HIDROLAVADORA.pdf | El aparato no funciona, Problemas de presión, etc. |
| **Generador Generac Guardian** | Generac_Manual_Usuario_Guardian_Series.pdf | Arranque, Funcionamiento, Mantenimiento |
| **Motor Cummins** | MANUAL CUMMINS 2.pdf | Problemas de arranque, Rendimiento, Consumo |
| **Soldadora Miller Ranger 305D** | ranger_305d.pdf | Conexión, Soldadura, Problemas eléctricos |

**Agregar nuevas máquinas:** Sube el PDF desde el dashboard admin y se genera automáticamente.

---

## 🚨 Solución de Problemas

### Python no reconocido

```powershell
# Agregar al PATH o instalar desde:
# https://www.python.org/downloads/
```

### pip no reconocido

```powershell
python -m pip install -r requirements.txt
```

### Puerto 8000 ocupado

```powershell
# Cambiar puerto al iniciar:
python -m uvicorn app:app --port 8001
```

### Módulos faltantes

```powershell
pip install -r requirements.txt
```

### Frontend no carga

- Verificar que el backend esté corriendo (`http://127.0.0.1:8000`)
- Limpiar caché del navegador (Ctrl+Shift+Del)
- Revisar la consola del navegador (F12)

### API devuelve error 404

- Verificar URL correcta
- Asegurarse que el backend esté corriendo
- Revisar spelling en parámetros (espacios, mayúsculas)

---

## 📚 Documentación Adicional

### Documentación Local

Para más detalles técnicos, consulta:

- **`INFORME_SISTEMA_EXPERTO.md`** (50+ páginas)
  - Arquitectura completa
  - Flujos detallados
  - Mejoras futuras
  - Casos de uso

- **`COMO_USAR.txt`**
  - Guía rápida
  - Credenciales
  - Máquinas disponibles

- **`docs/`** - Sitio MkDocs con documentación completa
  - `index.md` - Página de inicio
  - Instalación paso a paso
  - Uso del sistema
  - API reference
  - Solución de problemas
  - Informe del sistema experto

### Sitio Web de Documentación

El proyecto incluye un **sitio de documentación profesional con MkDocs** (Material theme):

```bash
# Instalar MkDocs (si no está instalado)
pip install mkdocs-material

# Generar y servir documentación localmente
mkdocs serve -a 127.0.0.1:8001

# Acceder a: http://127.0.0.1:8001/
```

**Características:**
- 🌓 Modo claro/oscuro
- 🎨 Tema Material Design
- 📱 Responsive (móvil/desktop)
- 🔍 Búsqueda integrada
- 🌐 Multiidioma (español)
- ✅ CI/CD con GitHub Actions (deploy automático)

---

## 🔮 Mejoras Futuras (Roadmap)

### Fase 2: Inteligencia Artificial (2-3 meses)
- 🚀 Análisis automático de PDFs con GPT-4/Claude
- 🚀 Generación inteligente de base de conocimiento
- 🚀 Extracción de información específica del manual

### Fase 3: Editor Visual (3-4 meses)
- 🚀 Interfaz gráfica para editar árbol de decisión
- 🚀 Validación automática
- 🚀 Vista previa de diagnósticos

### Fase 4: Machine Learning (4-6 meses)
- 🚀 Análisis de patrones de uso
- 🚀 Optimización automática del árbol
- 🚀 Predicción de fallas

### Fase 5: Integraciones (6-12 meses)
- 🚀 Integración con sistemas de tickets
- 🚀 Conexión con bases de datos de clientes
- 🚀 Aplicación móvil (iOS/Android)

Ver detalles completos en `INFORME_SISTEMA_EXPERTO.md`

---

## � CI/CD y Integración Continua

### GitHub Actions

El proyecto incluye **flujos de CI/CD automáticos** con GitHub Actions:

**`.github/workflows/ci.yml`** - Pipeline de despliegue:
- ✅ Se ejecuta en push a `master` o `main`
- ✅ Configura Python 3.x
- ✅ Instala MkDocs Material
- ✅ **Despliega automáticamente** la documentación a GitHub Pages
- ✅ Cache inteligente para optimizar builds

**Beneficios:**
- 📖 Documentación siempre actualizada
- 🚀 Despliegue automático sin intervención
- ⚡ Builds rápidos con caché
- 🔐 Seguridad integrada

---

## 👨‍💻 Equipo de Desarrollo

Este proyecto es parte de la **Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial** del Politécnico Malvinas Argentinas.

**Desarrolladores:**
- 👤 **Maximiliano Ruiz** - [maxi9304@gmail.com](mailto:maxi9304@gmail.com)
- 👤 **Yanina Barrios** - [yansolsur17@gmail.com](mailto:yansolsur17@gmail.com)
- 👤 **Mara Campos** - [maracampos671@gmail.com](mailto:maracampos671@gmail.com)
- 👤 **Pablo Jusin** - [pablo.jusin@gmail.com](mailto:pablo.jusin@gmail.com)
- 👤 **Marcelo Renzone** - [marcelorenzone@gmail.com](mailto:marcelorenzone@gmail.com)

---

Contribuciones bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit los cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📦 Dependencias

```
fastapi          # Framework web
uvicorn          # Servidor ASGI
python-multipart # Carga de archivos
python-jose      # Tokens JWT
jinja2           # Templating
reportlab        # Generación de PDFs (backend)
Flask            # Utilidades
werkzeug         # WSGI utilities
gunicorn         # Servidor producción (opcional)
```

Ver `requirements.txt` para versiones exactas.

---

## 📞 Soporte

### Documentación
- 📄 README.md (este archivo)
- 📄 INFORME_SISTEMA_EXPERTO.md
- 📄 COMO_USAR.txt

### Scripts de Inicio
- `INICIAR_BIG_TOOLS.bat` - Recomendado Windows
- `run.sh` - Linux/macOS
- `run_simple.py` - Multiplataforma

### Verificación Rápida

```powershell
# Verificar que todo funciona:
curl -s "http://127.0.0.1:8000/api/maquinas"

# Debe devolver JSON con lista de máquinas
```

---

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver detalles en el archivo LICENSE.

**Copyright © 2025 Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial - Politécnico Malvinas Argentinas**

---

## 👨‍💻 Desarrollo

**Tecnologías Usadas:**

- **Backend:** Python 3.8+, FastAPI, Uvicorn
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Base de Datos:** JSON (archivos locales)
- **Librerías Frontend:** Chart.js, jsPDF, Particles.js
- **Autenticación:** Tokens con SHA256

**Última Actualización:** Noviembre 2025  
**Versión:** 1.0.0  
**Estado:** Producción ✅

---

## 🎯 Comienza Ahora

### 3 pasos para empezar:

1. **Instala:** `pip install -r requirements.txt`
2. **Inicia:** `python -m uvicorn Backend/app:app --host 127.0.0.1 --port 8000`
3. **Accede:** Abre `http://127.0.0.1:8000` en tu navegador

### Login rápido:
- Usuario: `admin` / `tecnico`
- Contraseña: `1234`

---

## 👨‍💻👩‍💻 Desarrolladores
- **Maximiliano Ruiz:** [maxi9304@gmail.com](mailto:maxi9304@gmail.com)  
- **Yanina Barrios:** [yansolsur17@gmail.com](mailto:yansolsur17@gmail.com)  
- **Mara Campos:** [maracampos671@gmail.com](mailto:maracampos671@gmail.com)  
- **Pablo Jusin:** [pablo.jusin@gmail.com](mailto:pablo.jusin@gmail.com)  
- **Marcelo Renzone:** [marcelorenzone@gmail.com](mailto:marcelorenzone@gmail.com)

---
<div align="center">

**Desarrollado para Big Tools** - Sistema de Diagnóstico Industrial

Copyright © 2025 Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial - Politécnico Malvinas Argentinas

</div>

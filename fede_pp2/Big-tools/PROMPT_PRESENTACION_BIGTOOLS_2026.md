================================================================================
GUÍA COMPLETA DE LA PRESENTACIÓN: PROYECTO BIG TOOLS (TODOS LOS BLOQUES)
Versión actualizada — Arquitectura RAG Local (junio 2026)
================================================================================

NOTA PARA EL DISEÑADOR (Claude): Esta es la guía diapositiva por diapositiva para
diseñar la presentación de defensa del proyecto "Big Tools". El contenido técnico
refleja el estado REAL y actual del sistema: un Sistema Experto híbrido que combina
un árbol de diagnóstico guiado con un motor RAG (Retrieval-Augmented Generation)
que corre un modelo de lenguaje (LLM) 100% local y offline. Respetá la identidad
visual indicada en cada diapositiva, mantené la coherencia entre bloques y usá un
estilo moderno, técnico y profesional. Stack real a reflejar: Python + FastAPI,
ChromaDB (base vectorial local), Ollama ejecutando llama3.2:3b + embeddings
nomic-embed-text, PyMuPDF para el parseo de PDF, y frontend en HTML/CSS/JS
(tipografías Inter + Space Grotesk, fondo de partículas, selector "orbital" de
máquinas). NO mencionar servicios en la nube ni APIs externas: todo es offline.

================================================================================
BLOQUE 1: CONTEXTO E INSTITUCIÓN COFORMADORA
================================================================================

DIAPOSITIVA 1: PORTADA OFICIAL
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA:
  - BIG TOOLS
  - Sistema Experto Inteligente con IA Local para el Diagnóstico de Fallas Industriales
  - Contexto: Defensa de Prácticas Profesionalizantes II
  - Programa: Tecnicatura en Ciencia de Datos e Inteligencia Artificial
  - Institución: Centro Politécnico Superior Malvinas Argentinas
  - Autores (defensa grupal): Matias Espindola · Federico Solis · Nadia Pessina · Marta Cruz
  - Coordinador Académico: Federico Magaldi
* IDENTIDAD VISUAL: Fondo Oscuro (#232838), textos en Blanco y acentos en Rojo (#E91F26).
  Estética moderna: tipografía de títulos tipo "Space Grotesk", sutiles anillos/órbitas
  o partículas de fondo que evoquen la interfaz real de la app.
* UBICACIÓN DE LOGOS: Logo Institucional arriba a la izquierda; Logo Corporativo (Big Tools) arriba a la derecha.
* NOTAS DEL ORADOR: "Buenas tardes a los miembros del tribunal, profesores y coordinador presente. Somos el equipo que desarrolló 'Big Tools', y hoy les presentamos la defensa de nuestras Prácticas Profesionalizantes II. El proyecto es un Sistema Experto para el Diagnóstico de Fallas que incorpora inteligencia artificial generativa funcionando de forma totalmente local. Nace como respuesta a una necesidad real del sector de mantenimiento y postventa industrial, y aplica de manera directa herramientas de Ciencia de Datos e IA —procesamiento de lenguaje natural, búsqueda semántica y modelos de lenguaje— para optimizar procesos operativos críticos dentro de una organización coformadora."

DIAPOSITIVA 2: PRESENTACIÓN DE LA EMPRESA (ORGANIZACIÓN COFORMADORA)
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: La Organización Coformadora
* TEXTO EN PANTALLA:
  - ¿Quién es Big Tools?: Empresa dedicada a la venta, postventa y provisión de repuestos de maquinaria pesada e industrial.
  - Sectores Estratégicos que Atiende: Logística y Transporte, Construcción y Movimiento de Suelos, Mantenimiento en la Industria de Hidrocarburos.
  - Rol en el Proyecto: Organización coformadora activa. Provisión de infraestructura técnica, manuales de taller originales y validación de requerimientos de ingeniería.
* IDENTIDAD VISUAL: Fondo Claro, textos principales en Azul Marino (#232838) e íconos limpios.
* UBICACIÓN DE LOGOS: Logo de Big Tools estándar abajo a la derecha como firma.
* NOTAS DEL ORADOR: "Para entender el impacto del software, es fundamental conocer dónde se aplica. Big Tools es una organización clave en la región que brinda soluciones integrales en industrias exigentes como la de hidrocarburos, la construcción y la logística pesada, abarcando desde la venta hasta el soporte postventa de generadores, compresores, equipos de soldadura y flota pesada. La empresa actuó como nuestra organización coformadora: nos abrió las puertas de sus talleres y, de manera crucial, nos facilitó el acceso a su repositorio de manuales técnicos de ingeniería y nos permitió entrevistar a sus operarios para modelar el sistema."

DIAPOSITIVA 3: EL PROBLEMA (LÍNEA DE BASE)
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: El Desafío Operativo (Línea de Base)
* TEXTO EN PANTALLA:
  - Diagnóstico Manual Complejo: Manuales de taller extensos (cientos de páginas), en lenguaje técnico y frecuentemente en inglés.
  - Dependencia del Factor Humano: El conocimiento del comportamiento de cada máquina está centralizado en pocos técnicos senior.
  - Brecha de Capacitación: Dificultad y lentitud para transmitir ese conocimiento crítico a los técnicos nuevos o ingresantes.
  - Impacto Económico: Altos costos operativos derivados del tiempo de inactividad cuando una máquina crítica queda parada en el taller.
* IDENTIDAD VISUAL: Fondo Claro. Conceptos clave ("Pérdida de tiempo", "Máquina parada") destacados en Rojo (#E91F26).
* UBICACIÓN DE LOGOS: Logotipos discretos de pie de página. Imagen/Vector de engranaje o reloj de arena.
* NOTAS DEL ORADOR: "Durante el relevamiento inicial en el taller detectamos una problemática clara: cuando ingresa una maquinaria con una falla compleja, el diagnóstico se vuelve un cuello de botella. Los técnicos deben buscar información manualmente en documentos inmensos, muchas veces en inglés técnico. Esto genera una fuerte dependencia de la experiencia de los operarios más antiguos; si ellos no están disponibles, el proceso se demora. En la industria, cada minuto de una máquina parada se traduce en pérdidas económicas y retrasos logísticos. El problema no es la falta de información —la empresa tiene los manuales— sino la velocidad y eficiencia con la que se accede a ella."

DIAPOSITIVA 4: ÁMBITO Y OBJETIVOS GENERALES
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: Ámbito del Proyecto y Objetivos
* TEXTO EN PANTALLA:
  - Objetivo General: Desarrollar un Sistema Experto Inteligente e Interactivo, con IA generativa en un entorno 100% Offline, para optimizar los tiempos de resolución y diagnóstico de fallas mecánicas y electrónicas en el taller.
  - Objetivos Específicos:
    * Automatización: Parsear, segmentar e indexar de forma automatizada manuales técnicos complejos, incluyendo sus tablas de averías (síntoma → causa → solución).
    * Accesibilidad: Proveer una interfaz dual: un módulo de diagnóstico guiado paso a paso y un chat libre conversacional sobre los manuales.
    * Seguridad: Garantizar el resguardo absoluto de la propiedad intelectual de la empresa mediante procesamiento 100% local, sin enviar datos a la nube.
* IDENTIDAD VISUAL: Fondo Claro. Estructura simétrica en dos columnas. Íconos temáticos por objetivo (engranaje, chat, candado).
* NOTAS DEL ORADOR: "Frente a este escenario fijamos como Objetivo General el diseño e implementación de un Sistema Experto Inteligente, con la premisa fundamental de que funcione de manera completamente offline. Como objetivos específicos nos propusimos: primero, automatizar la ingesta de los manuales en PDF, procesando su texto y, especialmente, sus tablas de síntomas; segundo, construir una interfaz intuitiva apta para cualquier nivel técnico, que ofrezca tanto un flujo de preguntas guiadas como una consulta libre por chat; y tercero, asegurar que toda la información confidencial de Big Tools se mantenga protegida dentro de su propia infraestructura local, sin depender de conexiones a internet ni de servicios externos."

================================================================================
BLOQUE 2: PROCESO METODOLÓGICO Y GESTIÓN (SPRINTS)
================================================================================

DIAPOSITIVA 5: METODOLOGÍA DE TRABAJO Y ROLES DEL EQUIPO
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: Marco Metodológico y Espacios de Trabajo
* TEXTO EN PANTALLA:
  - Metodología Ágil (Scrum Adaptado): Desarrollo mediante Ciclos Incrementales (Sprints) enfocados en el valor para el taller.
  - Ecosistema Digital de Trabajo:
    * Google Drive: Centralización de documentación, minutas y activos de marca.
    * Trello: Tablero Kanban para el control visual de tareas y estados de avance.
    * GitHub: Repositorio centralizado para el control de versiones del código fuente.
* IDENTIDAD VISUAL: Fondo Claro. División visual limpia tipo bloques independientes. Íconos oficiales de Trello, GitHub y Drive.
* NOTAS DEL ORADOR: "Para llevar adelante el proyecto de manera ordenada, implementamos un marco de trabajo ágil basado en Scrum, adaptándolo a los tiempos de la cursada a través de Sprints. Esto nos permitió avanzar de forma incremental y flexible. Para sostener esta estructura configuramos un ecosistema digital integrado: usamos Trello como tablero Kanban para el seguimiento diario; GitHub como repositorio central de software, garantizando el control de versiones; y Google Drive como biblioteca documental, donde guardamos desde las actas de reuniones hasta los manuales originales provistos por el taller."

DIAPOSITIVA 6: SPRINT 1 — PLANIFICACIÓN Y ANÁLISIS INICIAL
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: Sprint 1: Planificación y Ámbito de Desarrollo
* TEXTO EN PANTALLA:
  - Objetivo: Establecer los cimientos operativos y definir el alcance técnico del sistema experto.
  - Hitos y Entregables Alcanzados:
    * Organización Interna: Definición de roles técnicos y canales de comunicación.
    * Espacios de Trabajo: Despliegue y vinculación de entornos en Drive, GitHub y Trello.
    * Análisis de Requerimientos: Relevamiento de la problemática y documentación técnica.
    * Definición del Alcance: Confección formal del Ámbito de Desarrollo y Diagrama de Gantt.
    * Formalización: Redacción y envío de la Carta de Presentación institucional.
* IDENTIDAD VISUAL: Fondo Claro. Formato de checklist institucional con tildes de completado. Miniatura del Gantt o tablero inicial a la derecha.
* NOTAS DEL ORADOR: "El Sprint 1 estuvo enfocado en la cimentación del proyecto. Las tareas clave fueron estructurar internamente los roles y desplegar la infraestructura digital de trabajo. El hito principal fue la investigación del problema para dar forma al documento de 'Ámbito de Desarrollo', donde delimitamos exactamente qué iba a hacer el sistema y diseñamos el Diagrama de Gantt para estimar los tiempos de entrega. El sprint concluyó con la entrega de las planificaciones y el envío de la carta de presentación que nos vinculó oficialmente con la organización coformadora."

DIAPOSITIVA 7: SPRINT 2 — ARQUITECTURA DE DATOS Y PROTOTIPO BACKEND
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: Sprint 2: Desarrollo Core y Validación de Ampliación
* TEXTO EN PANTALLA:
  - Objetivo: Construir la lógica central del procesamiento de datos y validar el rumbo técnico con la empresa.
  - Hitos y Entregables Alcanzados:
    * Módulos de Gestión Base: Lógica para registro de técnicos e ingesta de manuales.
    * Prototipo Backend: Motor base (pipeline de procesamiento de PDF y preparación del RAG).
    * Hito Clave - Reunión de Alineación: Presentación de avances ante los responsables del taller.
    * Ampliación del Alcance: Aprobación de la Propuesta de Ampliación de Desarrollo para integrar un LLM local (Ollama) y búsqueda semántica vectorial.
* IDENTIDAD VISUAL: Fondo Claro. Destacar "Ampliación de Desarrollo" o "Hito Clave" en Rojo (#E91F26).
* NOTAS DEL ORADOR: "Durante el Sprint 2 pasamos de la planificación a las líneas de código. Nos enfocamos en el núcleo del backend, estructurando la carga de los perfiles de los técnicos y el procesamiento inicial de los manuales con PyMuPDF. Un momento bisagra fue la reunión presencial con la institución coformadora: al presentarles el prototipo funcional y la capacidad de extracción de datos, surgió la oportunidad de llevar el proyecto al siguiente nivel. Propusimos una 'Ampliación de Desarrollo' para transicionar de un buscador de texto clásico hacia un motor RAG con un modelo de lenguaje local e interactivo. La propuesta fue aprobada, lo que redefinió positivamente el alcance tecnológico de las prácticas."

DIAPOSITIVA 8: SPRINT 3 — INTEGRACIÓN, TESTING Y CIERRE TÉCNICO
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: Sprint 3: Integración de Interfaz y Calibración Offline
* TEXTO EN PANTALLA:
  - Objetivo: Unificar las capas del sistema, validar la precisión de la IA local y congelar la versión final.
  - Hitos y Entregables Alcanzados:
    * Integración Fullstack: Conexión de la interfaz gráfica (Frontend) con el motor RAG local.
    * Procesamiento de Tablas: Calibración del extractor para reconstruir matrices Síntoma → Causa → Acción Correctiva por columnas.
    * Pruebas de Consistencia (Testing): Ajuste de los parámetros de recuperación (cantidad de fragmentos, umbral semántico) para mitigar alucinaciones y forzar la cita de la página exacta.
    * Optimización de Entorno: Pruebas de rendimiento del LLM local (llama3.2:3b) para garantizar respuestas veloces sin conexión.
* IDENTIDAD VISUAL: Fondo Claro. Estilo ejecutivo. Esquema de flujo sutil: Interfaz -> Motor RAG Local -> Manual PDF.
* NOTAS DEL ORADOR: "El Sprint 3 significó la integración final y la puesta a punto técnica. Conectamos la interfaz de usuario con nuestro motor RAG y nos concentramos en una tarea crítica de la Ciencia de Datos: el testing y la calibración. Los manuales industriales contienen tablas de averías complejas que suelen romperse al extraer el texto de forma ordinaria; dedicamos este sprint a ajustar los algoritmos para que el sistema reconstruyera correctamente esas relaciones de Síntoma-Causa-Solución, columna por columna. Además, calibramos los parámetros del RAG para que el modelo respondiera apoyándose solo en el manual, citando la página exacta de origen, y optimizamos la velocidad de inferencia en hardware local sin conexión externa."

================================================================================
BLOQUE 3: INGENIERÍA DE SOFTWARE Y DESARROLLO TÉCNICO
================================================================================

DIAPOSITIVA 9: EL CONCEPTO TÉCNICO (SISTEMA EXPERTO HÍBRIDO + RAG LOCAL)
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: Evolución Arquitectónica: Sistema Experto Híbrido con RAG Local
* TEXTO EN PANTALLA:
  - De Reglas Rígidas a IA con Contexto: Combinamos un árbol de decisión curado (diagnóstico guiado, confiable) con un motor RAG que entiende lenguaje natural sobre el manual.
  - Pipeline del Motor RAG Offline:
    1. Ingesta: Carga del manual PDF original con PyMuPDF.
    2. Segmentación (Chunking): División en fragmentos preservando la estructura de las tablas de averías.
    3. Embeddings Vectoriales: Conversión de texto y tablas a vectores semánticos con el modelo local nomic-embed-text (vía Ollama).
    4. Base de Datos Vectorial: Almacenamiento e indexado local en ChromaDB para búsquedas semánticas inmediatas.
    5. Recuperación + Generación: Ante una consulta, se recuperan los fragmentos más relevantes y se entregan como contexto exclusivo al LLM local (llama3.2:3b), que redacta la respuesta citando la página.
* IDENTIDAD VISUAL: Fondo Claro. Esquema de flujo horizontal secuencial con flechas. Bloques en Azul Marino (#232838) y el paso de Generación destacado en Rojo (#E91F26).
* NOTAS DEL ORADOR: "Acá es fundamental explicar la arquitectura interna del software. Tradicionalmente, los sistemas expertos se construían solo con árboles de decisión rígidos y reglas if-else escritas a mano, difíciles de mantener cuando ingresa una máquina nueva. Nosotros adoptamos un enfoque híbrido: para los equipos críticos mantenemos un árbol de conocimiento curado y confiable, pero lo potenciamos con un motor de Generación Aumentada por Recuperación —RAG— conectado a un LLM local. El flujo técnico procesa los PDFs del taller con PyMuPDF, divide el texto en fragmentos lógicos mediante chunking, y los convierte en embeddings vectoriales con un modelo de embeddings local. Esos vectores se almacenan en ChromaDB, nuestra base de datos vectorial. Cuando el técnico consulta, el sistema no adivina: busca matemáticamente los fragmentos más relevantes del manual y se los entrega al modelo como contexto exclusivo, lo que reduce las alucinaciones y obliga a fundamentar cada respuesta."

DIAPOSITIVA 10: ARQUITECTURA DEL SISTEMA, STACK Y SEGURIDAD
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: Stack Tecnológico y Pilares de Seguridad
* TEXTO EN PANTALLA:
  - Stack Tecnológico Core:
    * Python + FastAPI / Uvicorn: Backend y orquestación de la API y la IA.
    * Ollama (LLM Local): Ejecuta el modelo de lenguaje llama3.2:3b y los embeddings nomic-embed-text de forma offline.
    * ChromaDB: Base de datos vectorial local para indexación y búsqueda semántica de alta velocidad.
    * PyMuPDF: Parseo y extracción de texto y tablas de los manuales PDF.
    * Frontend (HTML/CSS/JS): Interfaz ágil e intuitiva (tipografías Inter + Space Grotesk, selector visual de máquinas), adaptada al operador de taller.
  - El Pilar Crítico: Seguridad e Independencia:
    * Operación 100% Offline: Sin dependencias de APIs externas ni consumo de internet.
    * Privacidad Absoluta: Los manuales de ingeniería y la propiedad intelectual se quedan estrictamente dentro de la infraestructura física de la empresa.
    * Sin Costos Recurrentes: Al no usar APIs de terceros, no hay costos por consulta ni por token.
* IDENTIDAD VISUAL: Fondo Claro. Dos columnas balanceadas: izquierda para Stack (logos limpios) y derecha para Seguridad (recuadro destacado con borde sutil).
* NOTAS DEL ORADOR: "Para materializar este diseño seleccionamos un stack robusto y eficiente. Usamos Python con FastAPI como base por su ecosistema avanzado en ciencia de datos. El modelo de lenguaje y los embeddings corren localmente a través de Ollama, y la base vectorial ChromaDB también vive en la máquina de destino. Pero el verdadero diferencial no es solo técnico, sino estratégico: la seguridad. En entornos industriales, los manuales de taller son activos críticos y confidenciales. Al estructurar un sistema cien por ciento offline, garantizamos que ningún dato sensible salga hacia la nube, eliminamos los costos recurrentes de APIs de terceros y blindamos la seguridad informática de Big Tools."

DIAPOSITIVA 11: EL PRODUCTO (ESTRUCTURA DE LA DEMO)
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: El Producto: Arquitectura de la Demo Funcional
* TEXTO EN PANTALLA:
  - Flujo de Usuario en 4 Pasos:
    1. Selector de Equipos: Pantalla de inicio con buscador y selector visual para localizar la maquinaria.
    2. Detección Automática de Interfaz: El sistema identifica solo qué modo corresponde a cada máquina:
       * Diagnóstico Guiado: Para equipos con árbol de conocimiento curado, cuestionario paso a paso (click en opciones). Al llegar a la solución, botón "Profundizar / Ampliar con IA".
       * Consulta Libre: Para manuales nuevos cargados por los técnicos, chat conversacional abierto sobre ese manual.
    3. Pantalla de Resultados: Causa Probable, Solución Sugerida y la cita con el número de página exacta del manual.
    4. Panel de Administración: Espacio para la carga de nuevos PDFs e indexación automatizada (con generación de un árbol borrador a partir de las tablas de averías para revisión humana).
* IDENTIDAD VISUAL: Fondo Claro. Captura grande de la interfaz real de la aplicación en el centro, con etiquetas explicativas de texto corto apuntando a cada función.
* NOTAS DEL ORADOR: "Ahora analizamos el producto final desde la perspectiva del operario. Diseñamos una experiencia limpia y directa, dividida en cuatro módulos. Al ingresar, el técnico se encuentra con un selector donde elige el equipo a reparar. El sistema detecta automáticamente el formato: si es un equipo crítico con árbol curado, inicia un diagnóstico guiado con preguntas secuenciales simples, y al llegar a la solución ofrece un botón para 'Ampliar con IA' que expande la explicación usando el LLM sobre el manual; si es un manual nuevo indexado por el equipo, abre una consulta libre por chat. La salida siempre acompaña la solución con la página exacta del manual para su validación. Y todo se cierra con un panel de administración que permite cargar nuevos PDFs para expandir el cerebro del asistente de manera automática."

================================================================================
BLOQUE 4: CONCLUSIONES FINALES
================================================================================

DIAPOSITIVA 12: RETROSPECTIVA Y CONFIGURACIÓN DEL SISTEMA
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: Configuración Local y Retrospectiva
* TEXTO EN PANTALLA:
  - Inicialización Automatizada: Despliegue local mediante un script unificado (`INICIAR_BIG_TOOLS.bat`) que verifica dependencias, levanta el servidor (Uvicorn) y abre el navegador con un solo clic.
  - Dinámica de Carga: Indexado automático al subir un nuevo PDF desde el panel de administración; el manual queda disponible para consulta en minutos.
  - Lecciones Aprendidas (Retrospectiva):
    * Desafío Técnico: Complejidad en la normalización y reconstrucción de tablas de averías multi-columna en PDFs antiguos o en inglés (se sumó traducción asistida de fragmentos EN→ES con el propio LLM).
    * Éxito Operativo: Adopción inmediata por parte de los técnicos gracias a una curva de aprendizaje mínima y respuestas en segundos, sin conexión.
* IDENTIDAD VISUAL: Fondo Claro. Bloques de tipo "terminal" o íconos de consola para la parte del `.bat`, y viñetas de análisis para el balance.
* NOTAS DEL ORADOR: "Para asegurar la viabilidad del proyecto dentro de los talleres de Big Tools, automatizamos todo el despliegue. Diseñamos un script ejecutable, 'INICIAR_BIG_TOOLS.bat', que verifica las dependencias, levanta el backend y la base vectorial, y abre la interfaz con un solo clic, sin que el personal necesite conocimientos de programación. Como retrospectiva, el mayor desafío técnico fue el parseo de las tablas de averías complejas o en formatos antiguos dentro de los PDFs; lo resolvimos reconstruyendo las tablas por columnas y, cuando el manual estaba en inglés, traduciendo los fragmentos al español con el mismo modelo local. La recompensa fue ver a los operarios adaptarse instantáneamente al sistema, validando que la IA puede integrarse al trabajo diario de manera práctica y segura."

DIAPOSITIVA 13: CONCLUSIONES Y AGRADECIMIENTOS
--------------------------------------------------------------------------------
* TÍTULO EN PANTALLA: Conclusiones y Cierre Institucional
* TEXTO EN PANTALLA:
  - Balance del Proyecto: Sistema experto funcional, escalable y privado, con un enfoque de IA de vanguardia (RAG + LLM local) adaptado a un negocio real.
  - Impacto en la Carrera: Consolidación práctica de los conocimientos en Ciencia de Datos e Inteligencia Artificial en un entorno productivo.
  - Agradecimientos:
    * A la organización coformadora Big Tools por su confianza, tutoría y apertura de infraestructura.
    * Al Centro Politécnico Superior Malvinas Argentinas y al cuerpo docente por el acompañamiento académico continuo.
* IDENTIDAD VISUAL: Fondo Oscuro (#232838) en sintonía con la portada. Títulos limpios en Blanco y cierre institucional formal.
* UBICACIÓN DE LOGOS: Logotipos institucionales y corporativos en el centro de la zona inferior.
* NOTAS DEL ORADOR: "Como conclusión, cerramos esta etapa habiendo entregado un sistema experto completamente funcional, privado y adaptable, que resuelve un dolor de cabeza diario en la postventa industrial. Para nosotros, estas prácticas fueron la oportunidad perfecta de consolidar cada asignatura de la Tecnicatura en Ciencia de Datos e Inteligencia Artificial, llevándola de la teoría del aula a los fierros del taller. No queremos finalizar sin agradecer profundamente a las autoridades de Big Tools por abrirnos sus puertas y confiar en nuestro criterio técnico, y por supuesto al Politécnico Malvinas Argentinas y a todo su equipo docente por guiarnos durante toda la carrera. Quedamos a disposición del tribunal para responder sus preguntas. Muchas gracias."

================================================================================
RESUMEN TÉCNICO DE REFERENCIA (para mantener coherencia en toda la presentación)
================================================================================
- Tipo de sistema: Sistema Experto HÍBRIDO (árbol de diagnóstico guiado + motor RAG con LLM local).
- Backend: Python, FastAPI, Uvicorn.
- IA local (Ollama): LLM llama3.2:3b para generación; nomic-embed-text para embeddings.
- Base vectorial: ChromaDB (local).
- Parseo PDF: PyMuPDF (fitz), con extracción especializada de tablas síntoma → causa → acción correctiva.
- Frontend: HTML/CSS/JS (Inter + Space Grotesk, fondo de partículas, selector visual de máquinas).
- Dos modos de uso: (1) Diagnóstico guiado por árbol curado, con botón "Ampliar con IA"; (2) Chat libre RAG sobre manuales nuevos. El sistema detecta solo cuál aplica.
- Garantías clave: 100% offline · datos nunca salen de la empresa · sin APIs externas · sin costos recurrentes · cada respuesta cita la página del manual.
- Inicio: script `INICIAR_BIG_TOOLS.bat` (un clic).
- NO mencionar: nube, APIs externas (OpenAI/Claude/GPT), ni el "SE Dinámico" (módulo descartado).
================================================================================

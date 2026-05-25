/* Big Tools - Chatbot + RAG */

// ========== PARTÍCULAS FLOTANTES (fondo orbit) ==========
function initParticles() {
  const canvas = document.getElementById('particles-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  // Partículas: puntos rojos semi-transparentes que suben lentamente
  const COUNT = 55;
  const particles = Array.from({ length: COUNT }, () => makeParticle(true));

  function makeParticle(randomY = false) {
    return {
      x:       Math.random() * canvas.width,
      y:       randomY ? Math.random() * canvas.height : canvas.height + 10,
      r:       Math.random() * 2.8 + 0.6,
      speedY:  -(Math.random() * 0.45 + 0.15),   // sube lento
      speedX:  (Math.random() - 0.5) * 0.3,
      opacity: Math.random() * 0.18 + 0.05,       // muy sutil sobre fondo gris
      opacityDelta: (Math.random() - 0.5) * 0.004,
    };
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach((p, i) => {
      // mover
      p.x += p.speedX;
      p.y += p.speedY;
      p.opacity += p.opacityDelta;
      if (p.opacity > 0.22) p.opacityDelta = -Math.abs(p.opacityDelta);
      if (p.opacity < 0.04) p.opacityDelta =  Math.abs(p.opacityDelta);

      // reciclar si sale por arriba
      if (p.y < -10) particles[i] = makeParticle(false);

      // dibujar
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(211,47,47,${p.opacity.toFixed(3)})`;
      ctx.fill();
    });
    requestAnimationFrame(animate);
  }

  animate();
}

window.addEventListener('load', initParticles);

// ========== ORBIT — CARRUSEL CIRCULAR ==========

const ORBIT_RADIUS = 155;
let _orbitSheet = null;  // stylesheet para keyframes dinámicos

/**
 * Construye el carrusel con la lista de máquinas.
 * @param {string[]} maquinas
 */
function buildOrbit(maquinas) {
  const spin = document.getElementById('orbit-spin');
  if (!spin) return;
  spin.innerHTML = '';   // limpiar si se llama de nuevo

  // Obtener stylesheet para insertar keyframes dinámicos
  // IMPORTANTE: no usar document.styleSheets[0] porque puede apuntar a una
  // hoja cross-origin (CDN Playfair) que lanza SecurityError en insertRule().
  if (!_orbitSheet) {
    let styleEl = document.getElementById('orbit-keyframes');
    if (!styleEl) {
      styleEl = document.createElement('style');
      styleEl.id = 'orbit-keyframes';
      document.head.appendChild(styleEl);
    }
    _orbitSheet = styleEl.sheet;
  }

  maquinas.forEach((nombre, i) => {
    const angle = (i * 360 / maquinas.length) - 90;
    const kfName = `orbit-kf-${i}`;

    // Keyframe: posiciona en el círculo + contra-rota para mantener la tarjeta upright
    if (_orbitSheet) {
      try {
        _orbitSheet.insertRule(`
          @keyframes ${kfName} {
            from { transform: rotate(${angle}deg) translateX(${ORBIT_RADIUS}px) rotate(${-angle}deg); }
            to   { transform: rotate(${angle}deg) translateX(${ORBIT_RADIUS}px) rotate(${-angle - 360}deg); }
          }
        `, _orbitSheet.cssRules.length);
      } catch(e) {}
    }

    const mc = document.createElement('div');
    mc.className = 'orbit-mc';
    mc.style.animation = `${kfName} 44s linear infinite`;
    mc.innerHTML = `
      <div class="orbit-mc-inner">
        <div class="mc-accent-line"></div>
        <div class="mc-name">${nombre}</div>
      </div>
    `;
    mc.addEventListener('click', () => orbitPickMachine(nombre));
    spin.appendChild(mc);
  });
}

/** Transición: selector → modo (después de elegir máquina) */
function orbitPickMachine(nombre) {
  sessionState.maquina = nombre;
  document.getElementById('orbit-machine-name').textContent = nombre;

  const sel  = document.getElementById('orbit-sel');
  const mode = document.getElementById('orbit-mode');

  sel.classList.add('orbit-exit-up');
  setTimeout(() => {
    sel.style.display = 'none';
    sel.classList.remove('orbit-exit-up');
    mode.style.display = 'flex';
    void mode.offsetWidth;
    mode.classList.add('orbit-enter-up');
    setTimeout(() => mode.classList.remove('orbit-enter-up'), 320);
  }, 240);
}

/** Botón "← Cambiar" / "← Volver a todas las máquinas" */
function orbitGoBack() {
  const sel  = document.getElementById('orbit-sel');
  const mode = document.getElementById('orbit-mode');

  mode.classList.add('orbit-exit-down');
  setTimeout(() => {
    mode.style.display = 'none';
    mode.classList.remove('orbit-exit-down');
    sel.style.display = 'flex';
    void sel.offsetWidth;
    sel.classList.add('orbit-enter-down');
    setTimeout(() => sel.classList.remove('orbit-enter-down'), 320);
  }, 240);
}

/** Reinicia el orbit completo (vuelve al selector) */
function orbitReiniciar() {
  sessionState.maquina = null;
  sessionState.categoria = null;
  _limpiarSesionRAGSilencioso();
  orbitGoBack();
}

/** Transición suave orbit-screen → chat-screen */
function _mostrarChat(callback) {
  const orbitEl = document.getElementById('orbit-screen');
  const chatEl  = document.getElementById('main-container');

  orbitEl.classList.add('screen-exit');
  setTimeout(() => {
    orbitEl.style.display = 'none';
    orbitEl.classList.remove('screen-exit');
    chatEl.style.display  = 'block';
    void chatEl.offsetWidth;
    chatEl.classList.add('screen-enter');
    setTimeout(() => {
      chatEl.classList.remove('screen-enter');
      if (callback) callback();
    }, 320);
  }, 260);
}

/** Transición chat → orbit */
function _volverAlOrbit() {
  const orbitEl = document.getElementById('orbit-screen');
  const chatEl  = document.getElementById('main-container');

  chatEl.classList.add('screen-exit');
  setTimeout(() => {
    chatEl.style.display   = 'none';
    chatEl.classList.remove('screen-exit');
    chatWindow.innerHTML   = '';
    // Resetear a selector (por si quedó en modo)
    document.getElementById('orbit-sel').style.display  = 'flex';
    document.getElementById('orbit-mode').style.display = 'none';
    orbitEl.style.display  = 'flex';
    void orbitEl.offsetWidth;
    orbitEl.classList.add('screen-enter');
    setTimeout(() => orbitEl.classList.remove('screen-enter'), 320);
  }, 260);
}

/** Inicia modo SE: muestra chat y arranca diagnóstico */
function startSEMode() {
  const maquina = sessionState.maquina;
  _mostrarChat(() => {
    handleMachineSelection(maquina);
  });
}

/** Inicia modo RAG: muestra chat y abre consulta libre directa */
async function startRAGMode() {
  const maquina = sessionState.maquina;
  _mostrarChat(async () => {
    addMessage(`Manual de <strong>${maquina}</strong> — consulta libre activa.`);
    await _iniciarSesionRAG(maquina);
    await mostrarInputRAG(maquina);
  });
}

/** Limpia sesión RAG sin agregar mensaje al chat */
async function _limpiarSesionRAGSilencioso() {
  if (!_ragSessionId) return;
  try {
    await fetch(`${API_URL}/rag/sesion/${_ragSessionId}`, { method: 'DELETE' });
  } catch(e) {}
  _ragSessionId = null;
}

/** Abre el modal con todos los manuales disponibles */
async function _abrirModalManuales() {
  const modal = document.getElementById('all-manuales-modal');
  const grid  = document.getElementById('all-manuales-grid');
  if (!modal || !grid) return;

  modal.style.display = 'flex';

  // Usar caché si está disponible, sino fetchear
  let maquinas = _todasLasMaquinas;
  if (!maquinas.length) {
    grid.innerHTML = '<p class="amc-loading">Cargando manuales...</p>';
    try {
      const res  = await fetch(`${API_URL}/maquinas`);
      const data = await res.json();
      maquinas = data.maquinas || [];
      _todasLasMaquinas = maquinas;
    } catch(e) {
      grid.innerHTML = '<p class="amc-loading" style="color:#c62828;">Error al cargar los manuales.</p>';
      return;
    }
  }

  if (maquinas.length === 0) {
    grid.innerHTML = '<p class="amc-loading">No hay manuales disponibles.</p>';
    return;
  }

  // El modal muestra TODOS los manuales (incluyendo los del orbit)
  // con un indicador visual para los top 7 que ya están en el orbit
  const top7 = new Set(maquinas.slice(0, 7));
  grid.innerHTML = '';
  maquinas.forEach(nombre => {
    const card = document.createElement('div');
    card.className = 'amc-card';
    const enOrbit = top7.has(nombre);
    card.innerHTML = `
      <div class="amc-accent"></div>
      <div class="amc-name">${nombre}</div>
      ${enOrbit ? '<div class="amc-badge">En órbita</div>' : ''}
    `;
    card.addEventListener('click', () => {
      modal.style.display = 'none';
      orbitPickMachine(nombre);
    });
    grid.appendChild(card);
  });
}

// ========== VARIABLES PRINCIPALES ==========
const chatWindow = document.getElementById("chat-window");
const resetBtn = document.getElementById("reset-button");

if (typeof window.API_URL === 'undefined') {
    window.API_URL = "http://127.0.0.1:8000/api";
}
const API_URL = window.API_URL;

let sessionState = {
  maquina: null,
  categoria: null,
  token: null,
  username: null,
  role: null
};

// ========== GESTIÓN DE AUTENTICACIÓN ==========

/**
 * Verifica con el backend si el token almacenado sigue siendo válido.
 * Usa fetch directo para no interferir con ningún interceptor.
 * Si no lo es, limpia localStorage y muestra login.
 */
async function _verificarTokenAlInicio(token) {
  try {
    const res = await fetch(`${API_URL}/admin/verify`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const data = await res.json();
      return data; // { valid: true, username, role }
    }
  } catch(e) {
    // Sin conexión al backend: dejar pasar y mostrar login
  }
  return null;
}

window.addEventListener('DOMContentLoaded', async () => {
  const token    = localStorage.getItem('chatbot_token');
  const username = localStorage.getItem('chatbot_username');
  const role     = localStorage.getItem('chatbot_role');

  if (token && username) {
    // Verificar que el token siga siendo válido antes de mostrar la app
    const verificado = await _verificarTokenAlInicio(token);
    if (verificado) {
      sessionState.token    = token;
      sessionState.username = verificado.username || username;
      sessionState.role     = verificado.role     || role || 'tecnico';
      mostrarChatbot();
    } else {
      // Token inválido/expirado: limpiar y mostrar login
      localStorage.removeItem('chatbot_token');
      localStorage.removeItem('chatbot_username');
      localStorage.removeItem('chatbot_role');
      mostrarLogin();
    }
  } else {
    mostrarLogin();
  }
});

function mostrarLogin() {
  document.getElementById('login-modal').style.display    = 'flex';
  document.getElementById('main-container').style.display = 'none';
  document.getElementById('orbit-screen').style.display   = 'none';
}

function mostrarChatbot() {
  document.getElementById('login-modal').style.display = 'none';

  // Sincronizar display del usuario en ambas pantallas
  const uname = sessionState.username;
  const chip  = document.getElementById('orbit-user-display');
  if (chip) chip.textContent = `Usuario: ${uname}`;
  const ud = document.getElementById('user-display');
  if (ud) ud.textContent = `Usuario: ${uname}`;

  // Botón admin: mostrar solo a admins
  const adminBtn      = document.getElementById('admin-button');
  const orbitAdminBtn = document.getElementById('orbit-admin-btn');
  if (sessionState.role === 'admin') {
    if (adminBtn)      adminBtn.style.display      = 'inline-block';
    if (orbitAdminBtn) orbitAdminBtn.style.display = 'inline-block';
  } else {
    if (adminBtn)      adminBtn.style.display      = 'none';
    if (orbitAdminBtn) orbitAdminBtn.style.display = 'none';
  }

  // Mostrar orbit screen (no el chat todavía)
  document.getElementById('main-container').style.display = 'none';
  const orbitEl = document.getElementById('orbit-screen');
  orbitEl.style.display = 'flex';

  // Cargar máquinas y construir el orbit (solo si no está ya construido)
  const spin = document.getElementById('orbit-spin');
  if (spin && spin.children.length === 0) {
    _cargarMaquinasOrbit();
  }
}

// Máquinas completas cacheadas para el modal
let _todasLasMaquinas = [];

async function _cargarMaquinasOrbit() {
  try {
    const res  = await fetch(`${API_URL}/maquinas`);
    const data = await res.json();
    _todasLasMaquinas = data.maquinas || [];
    // Orbit muestra solo las top 7 más consultadas (ya vienen ordenadas por popularidad)
    const top7 = _todasLasMaquinas.slice(0, 7);
    buildOrbit(top7);
  } catch(e) {
    console.error('Error cargando máquinas para orbit:', e);
  }
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const errorMsg = document.getElementById('login-error');
  
  try {
    const response = await fetch(`${API_URL}/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    
    if (response.ok && data.token) {
      sessionState.token = data.token;
      sessionState.username = username;
      sessionState.role = data.role || 'tecnico';
      
      localStorage.setItem('chatbot_token', data.token);
      localStorage.setItem('chatbot_username', username);
      localStorage.setItem('chatbot_role', data.role || 'tecnico');
      
      document.getElementById('username').value = '';
      document.getElementById('password').value = '';
      errorMsg.textContent = '';
      
      mostrarChatbot();
    } else {
      errorMsg.textContent = 'Error: Usuario o contraseña incorrectos';
    }
  } catch (error) {
    errorMsg.textContent = 'Error: No se pudo conectar con el servidor';
    console.error('Error en login:', error);
  }
});

document.getElementById('logout-button').addEventListener('click', () => {
  _confirmarLogout(async () => {
    try {
      await fetch(`${API_URL}/admin/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionState.token}` }
      });
    } catch (error) {
      console.error('Error en logout:', error);
    }
    _doLogout();
  });
});

// Logout desde el orbit screen
document.getElementById('orbit-logout-btn')?.addEventListener('click', () => {
  _confirmarLogout(async () => {
    try {
      await fetch(`${API_URL}/admin/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${sessionState.token}` }
      });
    } catch (error) {}
    _doLogout();
  });
});

/**
 * Muestra el modal de confirmación de logout.
 * @param {Function} onConfirm - callback ejecutado si el usuario confirma
 */
function _confirmarLogout(onConfirm) {
  const modal  = document.getElementById('logout-confirm-modal');
  const btnOk  = document.getElementById('logout-ok-btn');
  const btnCan = document.getElementById('logout-cancel-btn');
  if (!modal) { onConfirm(); return; }   // fallback si no existe el modal

  modal.style.display = 'flex';

  // Clonar botones para limpiar listeners anteriores
  const okNew  = btnOk.cloneNode(true);
  const canNew = btnCan.cloneNode(true);
  btnOk.replaceWith(okNew);
  btnCan.replaceWith(canNew);

  const cerrar = () => { modal.style.display = 'none'; };

  document.getElementById('logout-ok-btn').addEventListener('click', () => {
    cerrar();
    onConfirm();
  });
  document.getElementById('logout-cancel-btn').addEventListener('click', cerrar);
  modal.addEventListener('click', (e) => { if (e.target === modal) cerrar(); }, { once: true });
}

function _doLogout() {
  localStorage.removeItem('chatbot_token');
  localStorage.removeItem('chatbot_username');
  localStorage.removeItem('chatbot_role');
  sessionState.token = null;
  sessionState.username = null;
  sessionState.role = null;
  chatWindow.innerHTML = '';
  sessionState.maquina = null;
  sessionState.categoria = null;
  _ragSessionId = null;
  document.getElementById('orbit-screen').style.display = 'none';
  document.getElementById('main-container').style.display = 'none';
  mostrarLogin();
}

// Botón "← Máquinas" en el header del chat
document.getElementById('reset-button')?.addEventListener('click', () => {
  sessionState.maquina   = null;
  sessionState.categoria = null;
  _limpiarSesionRAGSilencioso();
  _volverAlOrbit();
});

// Botones SE y RAG del orbit-mode (se conectan después del DOM load)
window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('btn-se-mode')?.addEventListener('click',  () => startSEMode());
  document.getElementById('btn-rag-mode')?.addEventListener('click', () => startRAGMode());
  document.getElementById('orbit-more-btn')?.addEventListener('click', () => {
    _abrirModalManuales();
  });

  // Modal "Ver todos los manuales" — cerrar
  document.getElementById('all-manuales-close')?.addEventListener('click', () => {
    document.getElementById('all-manuales-modal').style.display = 'none';
  });
  document.getElementById('all-manuales-modal')?.addEventListener('click', (e) => {
    if (e.target === e.currentTarget) e.currentTarget.style.display = 'none';
  });
});

// ========== MENSAJES Y OPCIONES ==========

function addMessage(text, sender = "bot") {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", sender);
  messageDiv.innerHTML = text;
  chatWindow.appendChild(messageDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return messageDiv;
}

function addOptions(options, callback) {
  const optionsWrapper = document.createElement("div");
  optionsWrapper.classList.add("bot-options");

  if (options.length === 0) {
    addMessage("ADVERTENCIA: No hay más opciones. Contacte a soporte.");
    return;
  }

  options.forEach((opt) => {
    const btn = document.createElement("button");
    btn.classList.add("option-btn");
    btn.textContent = opt;
    btn.addEventListener("click", () => {
      // Deshabilitar todos los botones del grupo al elegir
      optionsWrapper.querySelectorAll("button").forEach(b => b.disabled = true);
      optionsWrapper.querySelectorAll("button").forEach(b => b.style.opacity = "0.5");
      btn.style.opacity = "1";
      btn.style.outline = "2px solid #d32f2f";
      addMessage(opt, "user");
      callback(opt);
    });
    optionsWrapper.appendChild(btn);
  });

  chatWindow.appendChild(optionsWrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ========== RAG — CONSULTA LIBRE ==========

/**
 * Muestra el botón de consulta libre al manual RAG
 * Se llama después de mostrar las categorías del sistema experto
 */
function mostrarBotonRAG(nombreMaquina) {
  const wrapper = document.createElement("div");
  wrapper.classList.add("rag-separator");

  wrapper.innerHTML = `
    <div class="rag-divider">
      <span>ó</span>
    </div>
    <button class="rag-btn" id="btn-consulta-libre">
      💬 Consulta libre al manual
    </button>
    <p class="rag-hint">Hacé una pregunta directa sobre el manual de la máquina</p>
  `;

  chatWindow.appendChild(wrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  document.getElementById("btn-consulta-libre").addEventListener("click", async () => {
    wrapper.remove();
    // Crear sesión ANTES de mostrar el input, así está lista cuando el usuario escribe
    await _iniciarSesionRAG(nombreMaquina);
    await mostrarInputRAG(nombreMaquina);
  });
}

/**
 * Muestra el input de texto libre para el RAG.
 * Si no hay sesión activa, crea una nueva.
 */
async function mostrarInputRAG(nombreMaquina) {
  // Sesión ya creada en el click del botón; solo crear si de alguna forma no existe
  if (!_ragSessionId) {
    await _iniciarSesionRAG(nombreMaquina);
  }

  const inputWrapper = document.createElement("div");
  inputWrapper.classList.add("rag-input-wrapper");
  inputWrapper.id = "rag-input-wrapper";

  inputWrapper.innerHTML = `
    <div class="rag-input-container">
      <textarea
        id="rag-pregunta"
        class="rag-textarea"
        placeholder="Describí el problema o hacé una pregunta sobre el manual..."
        rows="2"
      ></textarea>
      <div class="rag-input-actions">
        <button class="rag-send-btn" id="rag-send-btn">Consultar →</button>
        <button class="rag-nueva-btn" id="rag-nueva-btn" title="Limpiar historial y empezar de cero">🔄 Nueva conv.</button>
        <button class="rag-cancel-btn" id="rag-cancel-btn">Volver al diagnóstico</button>
      </div>
    </div>
  `;

  chatWindow.appendChild(inputWrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  setTimeout(() => document.getElementById("rag-pregunta")?.focus(), 100);

  document.getElementById("rag-pregunta").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      enviarConsultaRAG(nombreMaquina);
    }
  });

  document.getElementById("rag-send-btn").addEventListener("click", () => {
    enviarConsultaRAG(nombreMaquina);
  });

  document.getElementById("rag-nueva-btn").addEventListener("click", async () => {
    inputWrapper.remove();
    await _limpiarSesionRAG();
    addMessage("🔄 Nueva conversación iniciada. El asistente ya no recuerda los mensajes anteriores.");
    await mostrarInputRAG(nombreMaquina);
  });

  document.getElementById("rag-cancel-btn").addEventListener("click", async () => {
    inputWrapper.remove();
    await _limpiarSesionRAG();
    addMessage(`Volviendo al diagnóstico de <strong>${nombreMaquina}</strong>...`);
    handleMachineSelection(nombreMaquina);
  });
}

/**
 * Core interno: hace el fetch SSE y renderiza la respuesta en el chat.
 * @param {string}  nombreMaquina
 * @param {string}  pregunta       - texto a enviar al backend
 * @param {boolean} analisis       - true → modo análisis estructurado (gravedad + pasos)
 * @param {string}  headerLabel    - texto del encabezado de la burbuja de respuesta
 */
async function _streamConsultaRAG(nombreMaquina, pregunta, analisis = false, headerLabel = "📖 Respuesta del manual", onFin = null) {
  const preguntaOriginal = pregunta;  // capturar para feedback
  // Loading animado con etapas
  const loadingMsg = addMessage(`
    <div class="rag-loading">
      <span class="rag-loading-dot"></span>
      <span class="rag-loading-dot"></span>
      <span class="rag-loading-dot"></span>
      <span id="rag-loading-texto" style="margin-left:8px; color:#666;">🔍 Buscando en el manual...</span>
    </div>
  `);

  try {
    const response = await fetch(`${API_URL}/rag/consulta/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre_maquina: nombreMaquina, pregunta, analisis })
    });

    // ── Error HTTP ───────────────────────────────────────────────────────────
    if (!response.ok) {
      loadingMsg.remove();
      const data = await response.json().catch(() => ({}));
      if (response.status === 400 && data.detail?.includes("indexado")) {
        addMessage(`
          ⚠️ El manual de <strong>${nombreMaquina}</strong> todavía no fue procesado para consultas libres.<br>
          <em>Pedile al administrador que lo indexe desde el panel de administración.</em>
        `);
      } else {
        addMessage(`❌ Error: ${data.detail || "No se pudo consultar el manual."}`);
      }
      _mostrarOpcionesPostRAG(nombreMaquina);
      return;
    }

    // ── Contenedor de streaming ───────────────────────────────────────────
    const streamContainer = document.createElement("div");
    streamContainer.classList.add("message", "bot");

    const ragRespuesta = document.createElement("div");
    ragRespuesta.classList.add("rag-respuesta");
    if (analisis) ragRespuesta.classList.add("rag-respuesta-analisis");
    ragRespuesta.innerHTML = `
      <div class="rag-respuesta-header">${headerLabel}</div>
      <div class="rag-respuesta-texto"></div>
      <div class="rag-paginas-container"></div>
    `;
    streamContainer.appendChild(ragRespuesta);
    chatWindow.appendChild(streamContainer);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    const textEl    = ragRespuesta.querySelector(".rag-respuesta-texto");
    const paginasEl = ragRespuesta.querySelector(".rag-paginas-container");

    // ── Leer el stream SSE ────────────────────────────────────────────────
    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer    = "";
    let fullText  = "";
    let loadingRemoved = false;
    let esDesdeCache   = false;   // flag capturado del evento meta

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const ev = JSON.parse(line.slice(6));

          if (ev.tipo === "meta") {
            if (ev.paginas?.length > 0) {
              paginasEl.innerHTML =
                `<div class="rag-paginas">📄 Fuente: págs. ${ev.paginas.join(", ")}</div>`;
            }
            if (ev.secciones?.length > 0) {
              paginasEl.innerHTML +=
                `<div class="rag-secciones">📑 ${ev.secciones.join(" · ")}</div>`;
            }
            if (ev.confianza !== undefined) {
              paginasEl.innerHTML += _badgeConfianza(ev.confianza);
            }
            if (ev.desde_cache) {
              esDesdeCache = true;
              paginasEl.innerHTML += `<span class="cache-badge">⚡ Respuesta instantánea</span>`;
            }

          } else if (ev.tipo === "inicio_stream") {
            // Actualizar texto del loading — todavía visible
            const textoEl = document.getElementById("rag-loading-texto");
            if (textoEl) textoEl.textContent = "✍️ Escribiendo respuesta...";

          } else if (ev.tipo === "token") {
            // Primer token: recién ahora sacamos el loading
            if (!loadingRemoved) { loadingMsg.remove(); loadingRemoved = true; }
            fullText += ev.texto;
            textEl.innerHTML = _formatearRespuestaRAG(fullText, analisis);
            chatWindow.scrollTop = chatWindow.scrollHeight;

          } else if (ev.tipo === "error") {
            textEl.innerHTML += `<br><em style="color:#c62828;">❌ ${ev.mensaje}</em>`;

          } else if (ev.tipo === "respuesta_completa") {
            // Guardamos la respuesta para el feedback
            ragRespuesta._respuestaCompleta = ev.texto;

          } else if (ev.tipo === "fin") {
            // Agregar botones de feedback si hay respuesta (no en respuestas de cache)
            if (ragRespuesta._respuestaCompleta && !esDesdeCache) {
              _agregarBotonesFeedback(paginasEl, nombreMaquina, preguntaOriginal, ragRespuesta);
            }
            if (onFin) await onFin();
            else _mostrarOpcionesPostRAG(nombreMaquina);
          }
        } catch (_) { /* línea SSE malformada, ignorar */ }
      }
    }

  } catch (error) {
    loadingMsg.remove();
    addMessage(`❌ No se pudo conectar con el servidor. Verificá que esté corriendo.<br><em>${error.message}</em>`);
    console.error("Error RAG stream:", error);
  }
}

/**
 * Agrega los botones 👍/👎 debajo de una respuesta RAG.
 * Llama al backend y actualiza el cache semántico.
 */
function _agregarBotonesFeedback(paginasEl, maquina, pregunta, ragRespuesta) {
  const fb = document.createElement('div');
  fb.className = 'feedback-row';
  fb.innerHTML = `
    <span class="feedback-label">¿Fue útil esta respuesta?</span>
    <button class="feedback-btn feedback-pos" title="Sí, fue útil">👍</button>
    <button class="feedback-btn feedback-neg" title="No fue útil">👎</button>
  `;
  paginasEl.appendChild(fb);

  const enviarFeedback = async (positivo) => {
    // Deshabilitar botones inmediatamente
    fb.querySelectorAll('.feedback-btn').forEach(b => b.disabled = true);
    fb.querySelector('.feedback-label').textContent = positivo ? '✅ ¡Gracias!' : '📝 Anotado, lo tenemos en cuenta.';
    fb.querySelectorAll('.feedback-btn').forEach(b => b.style.display = 'none');

    try {
      await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionState.token}`
        },
        body: JSON.stringify({
          maquina,
          pregunta,
          respuesta: ragRespuesta._respuestaCompleta || '',
          positivo,
          confianza: parseInt(paginasEl.querySelector('.confidence-badge')?.textContent?.match(/\d+/)?.[0] || '75'),
          paginas:   [],
          secciones: [],
        })
      });
    } catch(e) {
      console.warn('Feedback no enviado:', e);
    }
  };

  fb.querySelector('.feedback-pos').addEventListener('click', () => enviarFeedback(true));
  fb.querySelector('.feedback-neg').addEventListener('click', () => enviarFeedback(false));
}

/**
 * ══ SE DINÁMICO ══
 * Inicia diagnóstico guiado para máquinas sin árbol estático.
 */
async function iniciarSEDinamico(nombreMaquina) {
  addMessage(`🔍 Iniciando diagnóstico guiado para <strong>${nombreMaquina}</strong>...`);
  sessionState.seDinamicoHistorial = [];
  sessionState.seDinamicoActivo    = true;

  try {
    const res  = await fetch(`${API_URL}/se-dinamico/iniciar/${encodeURIComponent(nombreMaquina)}`, {
      headers: { 'Authorization': `Bearer ${sessionState.token}` }
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Error al iniciar');

    _mostrarPasoSEDinamico(nombreMaquina, data.mensaje, data.opciones, data);
  } catch(e) {
    addMessage(`❌ No se pudo iniciar el diagnóstico: ${e.message}`);
  }
}

function _mostrarPasoSEDinamico(nombreMaquina, preguntaTexto, opciones, pasoData = {}) {
  const div = document.createElement('div');
  div.className = 'message bot sed-paso';

  const btnsHtml = (opciones || []).map(op =>
    `<button class="option-btn sed-opcion">${op}</button>`
  ).join('');

  div.innerHTML = `
    <div class="sed-pregunta">${preguntaTexto}</div>
    <div class="options-container">${btnsHtml}</div>
  `;

  div.querySelectorAll('.sed-opcion').forEach(btn => {
    btn.addEventListener('click', async () => {
      const respuesta = btn.textContent;
      // Deshabilitar opciones
      div.querySelectorAll('.sed-opcion').forEach(b => { b.disabled = true; b.style.opacity = '0.5'; });
      btn.style.opacity = '1'; btn.style.fontWeight = '700';
      addMessage(respuesta, 'user');
      await _avanzarSEDinamico(nombreMaquina, respuesta, preguntaTexto);
    });
  });

  document.getElementById('chat-window').appendChild(div);
  document.getElementById('chat-window').scrollTop = 99999;
}

async function _avanzarSEDinamico(nombreMaquina, respuestaUsuario, preguntaAnterior) {
  // Agregar al historial
  const hist = sessionState.seDinamicoHistorial;
  if (preguntaAnterior) hist.push({ rol: 'sistema', texto: preguntaAnterior });
  hist.push({ rol: 'usuario', texto: respuestaUsuario });

  const loadingMsg = addMessage('⚙️ Analizando...');

  try {
    const res  = await fetch(`${API_URL}/se-dinamico/paso/${encodeURIComponent(nombreMaquina)}`, {
      method: 'POST',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': `Bearer ${sessionState.token}`
      },
      body: JSON.stringify({
        historial_se:      hist,
        respuesta_usuario: respuestaUsuario,
      })
    });
    const data = await res.json();
    loadingMsg.remove();

    if (!res.ok) throw new Error(data.detail || 'Error');

    if (data.tipo === 'pregunta') {
      hist.push({ rol: 'sistema', texto: data.texto });
      _mostrarPasoSEDinamico(nombreMaquina, data.texto, data.opciones, data);

    } else if (data.tipo === 'diagnostico') {
      sessionState.seDinamicoActivo = false;
      const pags = data.paginas?.length
        ? `<div class="rag-paginas" style="margin-top:8px;">📄 Págs. ${data.paginas.join(', ')}</div>`
        : '';
      addMessage(`
        <div class="sed-diagnostico">
          <div class="sed-diag-header">🔧 Diagnóstico</div>
          <div class="sed-diag-body">${data.texto}</div>
          ${pags}
        </div>
      `);
      _mostrarOpcionesPostSE(nombreMaquina);

    } else {
      addMessage(`❌ ${data.texto || 'Error inesperado.'}`);
    }
  } catch(e) {
    loadingMsg.remove();
    addMessage(`❌ Error: ${e.message}`);
  }
}

function _mostrarOpcionesPostSE(nombreMaquina) {
  const div = document.createElement('div');
  div.className = 'message bot';
  div.innerHTML = `
    <div style="margin-bottom:8px;">¿Qué querés hacer ahora?</div>
    <div class="options-container">
      <button class="option-btn" id="sed-nuevo-diag">🔄 Nuevo diagnóstico</button>
      <button class="option-btn" id="sed-consulta-libre">📖 Consulta libre al manual</button>
      <button class="option-btn" id="sed-volver-maquinas">← Volver a máquinas</button>
    </div>
  `;
  document.getElementById('chat-window').appendChild(div);
  document.getElementById('chat-window').scrollTop = 99999;

  div.querySelector('#sed-nuevo-diag').addEventListener('click', () => {
    div.remove(); iniciarSEDinamico(nombreMaquina);
  });
  div.querySelector('#sed-consulta-libre').addEventListener('click', () => {
    div.remove();
    sessionState.modo = 'rag';
    iniciarModoRAG(nombreMaquina);
  });
  div.querySelector('#sed-volver-maquinas').addEventListener('click', () => {
    div.remove(); orbitReiniciar();
  });
}

/**
 * Genera el HTML del badge de confianza según el score (0-100).
 */
function _badgeConfianza(score) {
  let clase, etiqueta;
  if (score >= 75) {
    clase = "confianza-alta";   etiqueta = `✅ Confianza alta (${score}%)`;
  } else if (score >= 45) {
    clase = "confianza-media";  etiqueta = `⚠️ Confianza media (${score}%)`;
  } else {
    clase = "confianza-baja";   etiqueta = `❓ Confianza baja (${score}%) — revisá el manual`;
  }
  return `<div class="rag-confianza ${clase}">${etiqueta}</div>`;
}

/**
 * Formatea el texto de respuesta RAG para renderizado HTML.
 * En modo análisis resalta los encabezados estructurados.
 */
function _formatearRespuestaRAG(texto, analisis) {
  let html = texto.replace(/\n/g, "<br>");
  if (analisis) {
    // Resaltar los encabezados del análisis estructurado
    html = html.replace(/(GRAVEDAD:)/g, '<strong class="rag-label-gravedad">$1</strong>');
    html = html.replace(/(CAUSA PROBABLE:|RIESGO OPERACIONAL:|PASOS DE ACCIÓN:|REFERENCIA DEL MANUAL:)/g,
      '<strong class="rag-label-seccion">$1</strong>');
    // Colorear indicadores de gravedad
    html = html.replace(/🔴 CRÍTICO/g, '<span class="rag-gravedad critico">🔴 CRÍTICO</span>');
    html = html.replace(/🟡 MODERADO/g, '<span class="rag-gravedad moderado">🟡 MODERADO</span>');
    html = html.replace(/🟢 MENOR/g, '<span class="rag-gravedad menor">🟢 MENOR</span>');
  }
  return html;
}

// Patrones de mensajes conversacionales que no deben ir al RAG
const _SALUDOS = /^(hola|hello|hi|buenas|buen día|buen dia|buenas tardes|buenas noches|hey|cómo estás|como estas|qué tal|que tal|gracias|ok|dale|listo|perfecto|genial|bien|no|sí|si|claro|entendido|👍|👋)[\s!?.]*$/i;

// ── Sesión conversacional RAG ─────────────────────────────────────────────────
let _ragSessionId = null;   // null = sin sesión activa

async function _iniciarSesionRAG(nombreMaquina) {
  try {
    const res = await fetch(`${API_URL}/rag/sesion`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre_maquina: nombreMaquina })
    });
    const data = await res.json();
    _ragSessionId = data.session_id;
  } catch (e) {
    _ragSessionId = null;
    console.warn("No se pudo crear sesión RAG:", e);
  }
}

async function _limpiarSesionRAG() {
  if (!_ragSessionId) return;
  try {
    await fetch(`${API_URL}/rag/sesion/${_ragSessionId}`, { method: "DELETE" });
  } catch (_) {}
  _ragSessionId = null;
}

/**
 * Stream conversacional — usa el endpoint con memoria de sesión.
 * El LLM recibe el historial y actúa como agente diagnóstico.
 */
async function _streamConsultaConversacional(nombreMaquina, pregunta, onFin = null) {
  const loadingMsg = addMessage(`
    <div class="rag-loading">
      <span class="rag-loading-dot"></span>
      <span class="rag-loading-dot"></span>
      <span class="rag-loading-dot"></span>
      <span id="rag-loading-texto" style="margin-left:8px; color:#666;">🔍 Buscando en el manual...</span>
    </div>
  `);

  try {
    const response = await fetch(`${API_URL}/rag/consulta/conversacional`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nombre_maquina: nombreMaquina,
        pregunta,
        session_id: _ragSessionId
      })
    });

    if (!response.ok) {
      loadingMsg.remove();
      const data = await response.json().catch(() => ({}));
      if (response.status === 400 && data.detail?.includes("indexado")) {
        addMessage(`⚠️ El manual de <strong>${nombreMaquina}</strong> todavía no fue indexado.<br><em>Pedile al administrador que lo indexe desde el panel.</em>`);
      } else {
        addMessage(`❌ Error: ${data.detail || "No se pudo consultar el manual."}`);
      }
      if (onFin) await onFin();
      return;
    }

    // Contenedor de respuesta
    const streamContainer = document.createElement("div");
    streamContainer.classList.add("message", "bot");
    const ragRespuesta = document.createElement("div");
    ragRespuesta.classList.add("rag-respuesta");
    ragRespuesta.innerHTML = `
      <div class="rag-respuesta-header">🤖 Asistente diagnóstico</div>
      <div class="rag-respuesta-texto"></div>
      <div class="rag-paginas-container"></div>
    `;
    streamContainer.appendChild(ragRespuesta);
    chatWindow.appendChild(streamContainer);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    const textEl    = ragRespuesta.querySelector(".rag-respuesta-texto");
    const paginasEl = ragRespuesta.querySelector(".rag-paginas-container");

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer    = "";
    let fullText  = "";
    let loadingRemoved = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const ev = JSON.parse(line.slice(6));

          if (ev.tipo === "meta") {
            if (ev.paginas?.length > 0) {
              paginasEl.innerHTML = `<div class="rag-paginas">📄 Fuente: págs. ${ev.paginas.join(", ")}</div>`;
            }
            if (ev.secciones?.length > 0) {
              paginasEl.innerHTML += `<div class="rag-secciones">📑 ${ev.secciones.join(" · ")}</div>`;
            }
            if (ev.confianza !== undefined) {
              paginasEl.innerHTML += _badgeConfianza(ev.confianza);
            }
          } else if (ev.tipo === "inicio_stream") {
            const textoEl = document.getElementById("rag-loading-texto");
            if (textoEl) textoEl.textContent = "✍️ Escribiendo respuesta...";
          } else if (ev.tipo === "token") {
            if (!loadingRemoved) { loadingMsg.remove(); loadingRemoved = true; }
            fullText += ev.texto;
            textEl.innerHTML = fullText.replace(/\n/g, "<br>");
            chatWindow.scrollTop = chatWindow.scrollHeight;
          } else if (ev.tipo === "respuesta_completa") {
            // Detectar si es una pregunta de seguimiento y estilizarla
            const texto = ev.texto?.trim() || "";
            const esPregunta = texto.endsWith("?") ||
                               /^¿/.test(texto) ||
                               (texto.split("?").length === 2 && texto.length < 200);
            if (esPregunta) {
              ragRespuesta.classList.add("rag-followup");
              ragRespuesta.querySelector(".rag-respuesta-header").textContent = "❓ Necesito más información";
            }
          } else if (ev.tipo === "error") {
            textEl.innerHTML += `<br><em style="color:#c62828;">❌ ${ev.mensaje}</em>`;
          } else if (ev.tipo === "fin") {
            if (onFin) await onFin();
          }
        } catch (_) {}
      }
    }
  } catch (error) {
    loadingMsg.remove();
    addMessage(`❌ No se pudo conectar con el servidor.<br><em>${error.message}</em>`);
    console.error("Error RAG conversacional:", error);
  }
}

/**
 * Envía la consulta libre al endpoint RAG/stream (disparado por el textarea del usuario).
 * - Filtra mensajes conversacionales (saludos, respuestas cortas) sin llamar al backend.
 * - Vuelve a mostrar el input automáticamente después de cada respuesta.
 */
async function enviarConsultaRAG(nombreMaquina) {
  const textarea = document.getElementById("rag-pregunta");
  const pregunta = textarea?.value?.trim();

  if (!pregunta) {
    textarea?.classList.add("rag-textarea-error");
    setTimeout(() => textarea?.classList.remove("rag-textarea-error"), 1000);
    return;
  }

  const inputWrapper = document.getElementById("rag-input-wrapper");
  addMessage(pregunta, "user");
  inputWrapper?.remove();

  // ── Filtro: mensajes conversacionales ────────────────────────────────────
  if (_SALUDOS.test(pregunta) || pregunta.length < 4) {
    addMessage(`¡Hola! Estoy listo para responder tus preguntas sobre el manual de <strong>${nombreMaquina}</strong>. ¿En qué te ayudo?`);
    mostrarInputRAG(nombreMaquina);
    return;
  }

  // ── Consulta técnica → RAG conversacional (si hay sesión) o estándar ────────
  if (_ragSessionId) {
    await _streamConsultaConversacional(
      nombreMaquina,
      pregunta,
      () => mostrarInputRAG(nombreMaquina)
    );
  } else {
    await _streamConsultaRAG(
      nombreMaquina,
      pregunta,
      false,
      "📖 Respuesta del manual",
      () => mostrarInputRAG(nombreMaquina)
    );
  }
}

/**
 * Dispara un análisis profundo del manual para una falla detectada por el sistema experto.
 * Construye una consulta dirigida y activa el modo de análisis estructurado (gravedad + pasos).
 * @param {string} nombreMaquina
 * @param {string} falla  - descripción de la falla detectada por el sistema experto
 */
async function profundizarConIA(nombreMaquina, falla) {
  const pregunta = `Analizá en detalle la siguiente falla detectada en ${nombreMaquina}: "${falla}". `
    + `Explicá la causa técnica, el nivel de gravedad, si es seguro seguir operando, `
    + `y los pasos concretos para solucionar el problema según el manual.`;

  addMessage(
    `🔍 <strong>Profundizando con IA</strong> — analizando falla: <em>${falla}</em>`,
    "user"
  );

  await _streamConsultaRAG(
    nombreMaquina,
    pregunta,
    true,  // modo_analisis activo
    "🤖 Análisis técnico del manual"
  );
}

/**
 * Muestra los botones de acción después de recibir una respuesta RAG.
 */
function _mostrarOpcionesPostRAG(nombreMaquina) {
  const opcionesWrapper = document.createElement("div");
  opcionesWrapper.classList.add("bot-options");

  const btnOtra = document.createElement("button");
  btnOtra.classList.add("option-btn");
  btnOtra.textContent = "💬 Otra consulta al manual";
  btnOtra.addEventListener("click", async () => {
    opcionesWrapper.remove();
    await mostrarInputRAG(nombreMaquina);
  });

  const btnDiagnostico = document.createElement("button");
  btnDiagnostico.classList.add("option-btn");
  btnDiagnostico.textContent = "🔧 Ir al diagnóstico guiado";
  btnDiagnostico.addEventListener("click", () => {
    opcionesWrapper.remove();
    handleMachineSelection(nombreMaquina);
  });

  const btnReiniciar = document.createElement("button");
  btnReiniciar.classList.add("option-btn");
  btnReiniciar.textContent = "🔁 Consultar otra máquina";
  btnReiniciar.addEventListener("click", () => {
    opcionesWrapper.remove();
    startChat();
  });

  opcionesWrapper.appendChild(btnOtra);
  opcionesWrapper.appendChild(btnDiagnostico);
  opcionesWrapper.appendChild(btnReiniciar);
  chatWindow.appendChild(opcionesWrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ========== SISTEMA EXPERTO (sin cambios) ==========

function handleApiResponse(response) {
  if (response.pregunta && response.opciones) {
    addMessage(response.pregunta);
    addOptions(response.opciones, handleOptionSelection);
  }
  else if (response.falla && response.soluciones) {
    let solHTML = `<strong>Falla detectada:</strong> ${response.falla}<br>`;
    solHTML += "<strong>Soluciones sugeridas:</strong><ul>";
    response.soluciones.forEach((sol) => {
      solHTML += `<li>${sol}</li>`;
    });
    solHTML += "</ul>";

    if (response.referencia) {
      solHTML += `<br><em>(Ref: ${response.referencia})</em>`;
    }

    addMessage(solHTML);

    if (response.referencia && response.maquina) {
      const manualBtn = crearBotonManual(response.maquina, response.referencia);
      if (manualBtn) chatWindow.appendChild(manualBtn);
    }

    const diagnosticoData = {
      maquina: response.maquina || sessionState.maquina,
      categoria: sessionState.categoria,
      falla: response.falla,
      solucion: response.soluciones.join('. ')
    };
    const pdfBtn = crearBotonExportarPDF(diagnosticoData);
    chatWindow.appendChild(pdfBtn);

    // ── Botón "Profundizar con IA" ────────────────────────────────────────
    const maquinaActual = response.maquina || sessionState.maquina;
    if (maquinaActual && response.falla) {
      const profundizarWrapper = document.createElement("div");
      profundizarWrapper.classList.add("profundizar-wrapper");
      profundizarWrapper.innerHTML = `
        <div class="profundizar-hint">
          ¿Querés que la IA analice esta falla en profundidad usando el manual?
        </div>
        <button class="profundizar-btn" id="btn-profundizar-ia">
          🔍 Profundizar con IA
        </button>
      `;
      chatWindow.appendChild(profundizarWrapper);
      chatWindow.scrollTop = chatWindow.scrollHeight;

      document.getElementById("btn-profundizar-ia").addEventListener("click", () => {
        profundizarWrapper.remove();
        profundizarConIA(maquinaActual, response.falla);
      });
    }

    addOptions(["Consultar otra maquina"], startChat);
  }
  else {
    addMessage(response.mensaje || "Error inesperado en la respuesta.");
    addOptions(["🔁 Consultar otra máquina"], startChat);
  }
}

async function startChat() {
  // Vuelve al orbit selector en lugar de mostrar botones en el chat
  sessionState.maquina   = null;
  sessionState.categoria = null;
  await _limpiarSesionRAGSilencioso();
  _volverAlOrbit();
}

async function handleMachineSelection(machine) {
  sessionState.maquina = machine;

  try {
    const response = await fetch(`${API_URL}/categorias/${machine}`);
    const data = response.ok ? await response.json() : { categorias: [] };
    const cats = data.categorias || [];

    if (cats.length > 0) {
      // ── Máquina con árbol SE estático ─────────────────────────────────
      addMessage(`Elegiste <strong>${machine}</strong>. Seleccioná una categoría de diagnóstico:`);
      addOptions(cats, handleCategorySelection);
      mostrarBotonRAG(machine);
    } else {
      // ── Sin árbol estático → SE Dinámico respaldado por RAG ───────────
      addMessage(`
        <strong>${machine}</strong> — usando diagnóstico inteligente basado en el manual.
        <br><span style="font-size:.8rem;color:rgba(26,24,24,.45);">Este diagnóstico se genera en tiempo real consultando el manual indexado.</span>
      `);
      await iniciarSEDinamico(machine);
    }

  } catch (error) {
    addMessage(`ERROR: No se pudieron obtener las categorías: ${error.message}`);
  }
}

async function handleCategorySelection(category) {
  sessionState.categoria = category;
  addMessage(`Iniciando diagnóstico para: <strong>${category}</strong>`);

  try {
    const maquinaEncoded = encodeURIComponent(sessionState.maquina);
    const categoriaEncoded = encodeURIComponent(sessionState.categoria);
    const response = await fetch(
      `${API_URL}/diagnosticar/iniciar/${maquinaEncoded}/${categoriaEncoded}`,
      { method: "POST" }
    );
    
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al iniciar diagnóstico.");

    handleApiResponse(data);

  } catch (error) {
    addMessage(`ERROR: ${error.message}`);
    addOptions(["Consultar otra máquina"], startChat);
  }
}

async function handleOptionSelection(respuesta) {
  if (!sessionState.maquina || !sessionState.categoria) {
    addMessage("ERROR: Sesión inválida. Por favor, reinicia.");
    startChat();
    return;
  }

  try {
    const maquinaEncoded = encodeURIComponent(sessionState.maquina);
    const categoriaEncoded = encodeURIComponent(sessionState.categoria);
    const response = await fetch(
      `${API_URL}/diagnosticar/avanzar/${maquinaEncoded}/${categoriaEncoded}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ respuesta: respuesta }),
      }
    );

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Error al avanzar.");

    handleApiResponse(data);

  } catch (error) {
    addMessage(`ERROR: ${error.message}`);
    addOptions(["Consultar otra máquina"], startChat);
  }
}

// ========== EXPORTAR PDF (sin cambios) ==========

function crearBotonManual(maquina, referencia) {
  const manualesMap = {
    "hidrolavadora_karcher": "HIDROLAVADORA.pdf",
    "generador_generac": "Generac_Manual_Usuario_Guardian_Series (1).pdf",
    "motor_cummins": "MANUAL CUMMINS 2.pdf",
    "soldadora_miller_ranger": "ranger_305d.pdf"
  };

  const nombreTecnico = maquina.toLowerCase()
    .replace(/ /g, '_')
    .replace(/á/g, 'a').replace(/é/g, 'e').replace(/í/g, 'i')
    .replace(/ó/g, 'o').replace(/ú/g, 'u').replace(/ñ/g, 'n')
    .replace(/ä/g, 'a').replace(/ö/g, 'o').replace(/ü/g, 'u');

  const archivoManual = manualesMap[nombreTecnico];
  if (!archivoManual) return null;

  const container = document.createElement("div");
  container.classList.add("manual-button-container");

  const btn = document.createElement("a");
  btn.href = `/manuales/${encodeURIComponent(archivoManual)}`;
  btn.target = "_blank";
  btn.classList.add("manual-btn");
  btn.innerHTML = `📄 Ver Manual (${referencia})`;

  container.appendChild(btn);
  return container;
}

function crearBotonExportarPDF(data) {
  const container = document.createElement("div");
  container.classList.add("manual-button-container");

  const btn = document.createElement("button");
  btn.classList.add("manual-btn");
  btn.style.backgroundColor = "#2e7d32";
  btn.innerHTML = "⬇️ Exportar diagnóstico PDF";
  btn.addEventListener("click", () => exportarDiagnosticoPDF(data));

  container.appendChild(btn);
  return container;
}

function exportarDiagnosticoPDF(data) {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  let y = 20;

  doc.setFillColor(211, 47, 47);
  doc.rect(0, 0, pageWidth, 35, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(18);
  doc.setFont("helvetica", "bold");
  doc.text("BIG TOOLS", 25, 15);
  doc.setFontSize(12);
  doc.setFont("helvetica", "normal");
  doc.text("Sistema Experto de Diagnóstico", 25, 25);

  const now = new Date();
  doc.setFontSize(9);
  doc.text(`${now.toLocaleDateString('es-AR')} ${now.toLocaleTimeString('es-AR')}`, pageWidth - 25, 18, { align: 'right' });

  if (sessionState.username) {
    doc.text(`Usuario: ${sessionState.username}`, pageWidth - 25, 25, { align: 'right' });
  }

  y = 50;

  doc.setFillColor(211, 47, 47);
  doc.rect(20, y, pageWidth - 40, 8, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("INFORMACIÓN DEL EQUIPO", 25, y + 5.5);

  y += 15;
  doc.setTextColor(0, 0, 0);
  doc.setFontSize(10);

  if (data.maquina) {
    doc.setFont("helvetica", "bold");
    doc.text("Máquina:", 25, y);
    doc.setFont("helvetica", "normal");
    doc.text(data.maquina, 70, y);
    y += 7;
  }

  if (data.categoria) {
    doc.setFont("helvetica", "bold");
    doc.text("Categoría:", 25, y);
    y += 7;
    doc.setFont("helvetica", "normal");
    const categoriaLines = doc.splitTextToSize(data.categoria, pageWidth - 55);
    doc.text(categoriaLines, 25, y);
    y += (categoriaLines.length * 6) + 5;
  }

  y += 5;
  doc.setFillColor(211, 47, 47);
  doc.rect(20, y, pageWidth - 40, 8, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("DIAGNÓSTICO", 25, y + 5.5);

  y += 15;
  doc.setTextColor(0, 0, 0);
  doc.setFontSize(10);

  if (data.falla) {
    const fallaLines = doc.splitTextToSize(data.falla, pageWidth - 60);
    const boxHeight = (fallaLines.length * 6) + 10;
    doc.setDrawColor(211, 47, 47);
    doc.setLineWidth(0.5);
    doc.setFillColor(255, 240, 240);
    doc.rect(25, y - 3, pageWidth - 50, boxHeight, 'FD');
    doc.setFont("helvetica", "normal");
    doc.text(fallaLines, 30, y + 3);
    y += boxHeight + 10;
  }

  doc.setFillColor(46, 125, 50);
  doc.rect(20, y, pageWidth - 40, 8, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("SOLUCIÓN RECOMENDADA", 25, y + 5.5);

  y += 15;
  doc.setTextColor(0, 0, 0);
  doc.setFontSize(10);

  if (data.solucion) {
    const solucionLines = doc.splitTextToSize(data.solucion, pageWidth - 60);
    const boxHeight = (solucionLines.length * 6) + 10;
    doc.setDrawColor(46, 125, 50);
    doc.setLineWidth(0.5);
    doc.setFillColor(240, 255, 240);
    doc.rect(25, y - 3, pageWidth - 50, boxHeight, 'FD');
    doc.setFont("helvetica", "normal");
    doc.text(solucionLines, 30, y + 3);
    y += boxHeight + 10;
  }

  const footerY = pageHeight - 15;
  doc.setDrawColor(211, 47, 47);
  doc.setLineWidth(0.5);
  doc.line(20, footerY - 5, pageWidth - 20, footerY - 5);
  doc.setFontSize(8);
  doc.setTextColor(100, 100, 100);
  doc.setFont("helvetica", "italic");
  doc.text("Big Tools - Sistema Experto de Diagnóstico", 25, footerY);
  doc.text("Página 1 de 1", pageWidth - 25, footerY, { align: 'right' });

  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  doc.save(`BigTools_Diagnostico_${timestamp}.pdf`);
}

function iniciarChatbot() {
  // Reemplazado por el orbit selector — se mantiene por compatibilidad
  startChat();
}
// El resetBtn ahora está manejado más arriba con _volverAlOrbit()

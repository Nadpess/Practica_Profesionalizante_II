// ------------------------------------
// Big Tools - Panel de Administración
// ------------------------------------

// API_URL se carga desde config.js - si no está definida, usar valor por defecto
if (typeof window.API_URL === 'undefined') {
    window.API_URL = "http://127.0.0.1:8000/api";
}
// Usar la variable global
const API_URL = window.API_URL;

// Elementos del DOM
const dashboard = document.getElementById("dashboard");
const usernameDisplay = document.getElementById("username-display");
const logoutButton = document.getElementById("logout-button");
const refreshButton = document.getElementById("refresh-button");
const exportPdfButton = document.getElementById("export-pdf-button");

// Variable global para almacenar las estadísticas actuales
let estadisticasActuales = null;

// -----------------------------------------
// GESTIÓN DE AUTENTICACIÓN
// -----------------------------------------

// Verificar si hay sesión activa al cargar la página
function verificarSesion() {
  const token = localStorage.getItem("chatbot_token");
  const username = localStorage.getItem("chatbot_username");
  const role = localStorage.getItem("chatbot_role");

  if (!token || !username) {
    // No hay sesión, redirigir al login principal
    alert("ADVERTENCIA: Debes iniciar sesión primero");
    window.location.href = "/";
    return;
  }

  // Verificar que sea admin
  if (role !== "admin") {
    alert("ACCESO DENEGADO: Solo administradores pueden acceder al dashboard.");
    window.location.href = "/";
    return;
  }

  // Usuario admin autenticado, mostrar dashboard
  mostrarDashboard(username);
  cargarEstadisticas();
}

function mostrarDashboard(username) {
  dashboard.style.display = "block";
  usernameDisplay.textContent = `Usuario: ${username}`;
}

// -----------------------------------------
// MANEJO DE LOGOUT
// -----------------------------------------

logoutButton.addEventListener("click", async () => {
  if (confirm("¿Deseas cerrar sesión y volver al chatbot?")) {
    const token = localStorage.getItem("chatbot_token");

    if (token) {
      try {
        await fetch(`${API_URL}/admin/logout`, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });
      } catch (error) {
        console.error("Error al cerrar sesión:", error);
      }
    }

    // Limpiar localStorage
    localStorage.removeItem("chatbot_token");
    localStorage.removeItem("chatbot_username");
    localStorage.removeItem("chatbot_role");

    // Redirigir al login principal
    window.location.href = "/";
  }
});

// -----------------------------------------
// CARGAR ESTADÍSTICAS
// -----------------------------------------

async function cargarEstadisticas() {
  const token = localStorage.getItem("chatbot_token");

  if (!token) {
    alert("ADVERTENCIA: Sesión expirada");
    window.location.href = "/";
    return;
  }

  try {
    const response = await fetch(`${API_URL}/admin/stats`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Error al cargar estadísticas");
    }

    const stats = await response.json();

    // Actualizar las estadísticas en el DOM
    actualizarEstadisticas(stats);
    
  } catch (error) {
    console.error("Error al cargar estadísticas:", error);
    alert("ERROR: No se pudieron cargar las estadísticas");
  }
}

// -----------------------------------------
// ACTUALIZAR ESTADÍSTICAS EN EL DOM
// -----------------------------------------

function actualizarEstadisticas(stats) {
  // Guardar estadísticas globalmente para exportar a PDF
  estadisticasActuales = stats;
  
  // Total de diagnósticos
  document.getElementById("total-diagnosticos").textContent =
    stats.total_diagnosticos || 0;

  // Top máquinas
  const topMaquinasDiv = document.getElementById("top-maquinas");
  if (stats.top_maquinas && stats.top_maquinas.length > 0) {
    topMaquinasDiv.innerHTML = stats.top_maquinas
      .map(
        (item, index) => `
        <div class="stat-item">
          <span class="stat-rank">${index + 1}.</span>
          <span class="stat-name">${item.maquina}</span>
          <span class="stat-value">${item.cantidad} consultas</span>
        </div>
      `
      )
      .join("");
  } else {
    topMaquinasDiv.innerHTML = "<p class='no-data'>No hay datos disponibles</p>";
  }

  // Top categorías
  const topCategoriasDiv = document.getElementById("top-categorias");
  if (stats.top_categorias && stats.top_categorias.length > 0) {
    topCategoriasDiv.innerHTML = stats.top_categorias
      .map(
        (item, index) => `
        <div class="stat-item">
          <span class="stat-rank">${index + 1}.</span>
          <span class="stat-name">${item.categoria}</span>
          <span class="stat-detail">(${item.maquina})</span>
          <span class="stat-value">${item.cantidad} consultas</span>
        </div>
      `
      )
      .join("");
  } else {
    topCategoriasDiv.innerHTML = "<p class='no-data'>No hay datos disponibles</p>";
  }

  // Historial reciente
  const historialDiv = document.getElementById("historial-reciente");
  if (stats.historial_reciente && stats.historial_reciente.length > 0) {
    historialDiv.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Fecha/Hora</th>
            <th>Máquina</th>
            <th>Categoría</th>
            <th>Estado</th>
            <th>Falla Detectada</th>
          </tr>
        </thead>
        <tbody>
          ${stats.historial_reciente
            .map(
              (item) => `
            <tr>
              <td>${formatearFecha(item.timestamp)}</td>
              <td>${item.maquina}</td>
              <td>${item.categoria}</td>
              <td>
                <span class="badge ${item.completado ? "completed" : "pending"}">
                  ${item.completado ? "Completado" : "En proceso"}
                </span>
              </td>
              <td>${item.falla || "-"}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `;
  } else {
    historialDiv.innerHTML = "<p class='no-data'>No hay historial disponible</p>";
  }
  
  // ── RAG stats ─────────────────────────────────────────────────────────────
  const totalRAGEl = document.getElementById("total-rag");
  if (totalRAGEl) totalRAGEl.textContent = stats.total_consultas_rag || 0;

  const topRAGDiv = document.getElementById("top-maquinas-rag");
  if (topRAGDiv) {
    if (stats.top_maquinas_rag && stats.top_maquinas_rag.length > 0) {
      topRAGDiv.innerHTML = stats.top_maquinas_rag
        .map((item, index) => `
          <div class="stat-item">
            <span class="stat-rank">${index + 1}.</span>
            <span class="stat-name">${item.maquina}</span>
            <span class="stat-value">${item.cantidad} consultas</span>
          </div>`)
        .join("");
    } else {
      topRAGDiv.innerHTML = "<p class='no-data'>No hay consultas RAG registradas</p>";
    }
  }

  // Crear gráficos con un pequeño delay para asegurar que el DOM esté listo
  setTimeout(() => {
    crearGraficos(stats);
  }, 100);
}

// -----------------------------------------
// GRAFICOS CON CHART.JS
// -----------------------------------------

let chartMaquinas, chartCategorias, chartTendencia;

function crearGraficos(stats) {
  // Verificar que Chart.js esté cargado
  if (typeof Chart === 'undefined') {
    return;
  }

  // Destruir gráficos anteriores si existen
  if (chartMaquinas) chartMaquinas.destroy();
  if (chartCategorias) chartCategorias.destroy();
  if (chartTendencia) chartTendencia.destroy();

  // Verificar que los canvas existan
  const canvasMaquinas = document.getElementById('chartMaquinas');
  const canvasCategorias = document.getElementById('chartCategorias');
  const canvasTendencia = document.getElementById('chartTendencia');
  
  if (!canvasMaquinas || !canvasCategorias || !canvasTendencia) {
    return;
  }

  // Gráfico de Máquinas (Barras)
  const ctxMaquinas = canvasMaquinas.getContext('2d');
  const maquinasData = stats.top_maquinas || [];
  
  chartMaquinas = new Chart(ctxMaquinas, {
    type: 'bar',
    data: {
      labels: maquinasData.map(item => item.maquina),
      datasets: [{
        label: 'Diagnosticos',
        data: maquinasData.map(item => item.cantidad),
        backgroundColor: [
          'rgba(211, 47, 47, 0.7)',
          'rgba(33, 33, 33, 0.7)',
          'rgba(245, 124, 0, 0.7)',
          'rgba(56, 142, 60, 0.7)'
        ],
        borderColor: [
          'rgba(211, 47, 47, 1)',
          'rgba(33, 33, 33, 1)',
          'rgba(245, 124, 0, 1)',
          'rgba(56, 142, 60, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      }
    }
  });

  // Gráfico de Categorías (Dona)
  const ctxCategorias = canvasCategorias.getContext('2d');
  const categoriasData = stats.top_categorias || [];
  
  chartCategorias = new Chart(ctxCategorias, {
    type: 'doughnut',
    data: {
      labels: categoriasData.map(item => item.categoria),
      datasets: [{
        data: categoriasData.map(item => item.cantidad),
        backgroundColor: [
          'rgba(211, 47, 47, 0.7)',
          'rgba(33, 33, 33, 0.7)',
          'rgba(245, 124, 0, 0.7)',
          'rgba(56, 142, 60, 0.7)',
          'rgba(25, 118, 210, 0.7)'
        ],
        borderColor: [
          'rgba(211, 47, 47, 1)',
          'rgba(33, 33, 33, 1)',
          'rgba(245, 124, 0, 1)',
          'rgba(56, 142, 60, 1)',
          'rgba(25, 118, 210, 1)'
        ],
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right'
        }
      }
    }
  });

  // Gráfico de Tendencia (Línea)
  const ctxTendencia = canvasTendencia.getContext('2d');
  const historialData = stats.historial_reciente || [];
  
  // Agrupar por fecha
  const diagnosticosPorFecha = {};
  historialData.forEach(item => {
    const fecha = new Date(item.timestamp).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
    diagnosticosPorFecha[fecha] = (diagnosticosPorFecha[fecha] || 0) + 1;
  });
  
  // Ordenar fechas cronológicamente
  const fechasOrdenadas = Object.keys(diagnosticosPorFecha).sort((a, b) => {
    const [diaA, mesA, anioA] = a.split('/');
    const [diaB, mesB, anioB] = b.split('/');
    return new Date(anioA, mesA - 1, diaA) - new Date(anioB, mesB - 1, diaB);
  });
  
  // Tomar las últimas 10 fechas
  const fechas = fechasOrdenadas.slice(-10);
  const cantidades = fechas.map(fecha => diagnosticosPorFecha[fecha]);
  
  // Si no hay datos, mostrar un punto de ejemplo
  if (fechas.length === 0) {
    fechas.push('Sin datos');
    cantidades.push(0);
  }
  
  // Determinar el tipo de gráfico según la cantidad de datos
  const tipoGrafico = fechas.length === 1 ? 'bar' : 'line';
  
  chartTendencia = new Chart(ctxTendencia, {
    type: tipoGrafico,
    data: {
      labels: fechas,
      datasets: [{
        label: 'Diagnosticos',
        data: cantidades,
        borderColor: 'rgba(211, 47, 47, 1)',
        backgroundColor: tipoGrafico === 'bar' ? 'rgba(211, 47, 47, 0.8)' : 'rgba(211, 47, 47, 0.1)',
        tension: 0.3,
        fill: true,
        pointBackgroundColor: 'rgba(211, 47, 47, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 3,
        pointRadius: 8,
        pointHoverRadius: 10,
        borderWidth: 3,
        barThickness: 80
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          enabled: true,
          mode: 'index',
          intersect: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1,
            precision: 0
          },
          grid: {
            display: true,
            color: 'rgba(0, 0, 0, 0.1)'
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
      }
    }
  });
}

// -----------------------------------------
// UTILIDADES
// -----------------------------------------

function formatearFecha(isoString) {
  const fecha = new Date(isoString);
  const dia = String(fecha.getDate()).padStart(2, "0");
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const anio = fecha.getFullYear();
  const horas = String(fecha.getHours()).padStart(2, "0");
  const minutos = String(fecha.getMinutes()).padStart(2, "0");
  return `${dia}/${mes}/${anio} ${horas}:${minutos}`;
}

// -----------------------------------------
// BOTÓN DE ACTUALIZACIÓN
// -----------------------------------------

refreshButton.addEventListener("click", async () => {
  const token = localStorage.getItem("chatbot_token");
  if (token) {
    // Deshabilitar botón y mostrar feedback
    refreshButton.disabled = true;
    refreshButton.textContent = "Actualizando...";
    
    try {
      await cargarEstadisticas();
      
      // Mostrar mensaje de éxito
      refreshButton.textContent = "Actualizado";
      refreshButton.style.backgroundColor = "#4caf50";
      
      // Restaurar botón después de 1 segundo
      setTimeout(() => {
        refreshButton.textContent = "Actualizar Estadísticas";
        refreshButton.style.backgroundColor = "";
        refreshButton.disabled = false;
      }, 1000);
      
    } catch (error) {
      // Mostrar error
      refreshButton.textContent = "Error al actualizar";
      refreshButton.style.backgroundColor = "#f44336";
      
      setTimeout(() => {
        refreshButton.textContent = "Actualizar Estadísticas";
        refreshButton.style.backgroundColor = "";
        refreshButton.disabled = false;
      }, 2000);
    }
  } else {
    alert("No hay sesión activa. Por favor, inicie sesión.");
  }
});

// -----------------------------------------
// GESTIÓN DE PESTAÑAS
// -----------------------------------------

function inicializarPestanas() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      // Remover clase active de todos los botones y contenidos
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));

      // Agregar clase active al botón clickeado
      btn.classList.add("active");

      // Mostrar el contenido correspondiente
      const tabName = btn.getAttribute("data-tab");
      const tabContent = document.getElementById(`tab-${tabName}`);
      if (tabContent) {
        tabContent.classList.add("active");
      }

      // Si se abre la pestaña de manuales, cargar la lista
      if (tabName === "manuales") {
        cargarListaManuales();
      }
      // Si se abre la pestaña RAG, cargar el estado
      if (tabName === "rag") {
        cargarEstadoRAG();
      }
      // Si se abre el Debug RAG, cargar las máquinas indexadas
      if (tabName === "debug") {
        cargarMaquinasDebug();
      }
    });
  });
}

// -----------------------------------------
// GESTIÓN DE MANUALES
// -----------------------------------------

async function cargarListaManuales() {
  const manualesLista = document.getElementById("manuales-lista");
  
  console.log("Cargando lista de manuales...");
  
  try {
    const token = localStorage.getItem("chatbot_token");
    console.log("Token:", token ? "Presente" : "No encontrado");
    
    const response = await fetch("http://127.0.0.1:8000/api/admin/manuales", {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    
    console.log("Respuesta del servidor:", response.status);

    if (!response.ok) {
      throw new Error("Error al cargar manuales");
    }

    const data = await response.json();
    const manuales = data.manuales || [];

    if (manuales.length === 0) {
      manualesLista.innerHTML = "<p class='no-data'>No hay manuales disponibles. Sube tu primer manual usando el formulario de arriba.</p>";
      return;
    }

    manualesLista.innerHTML = manuales
      .map(
        (manual) => {
          const fecha = manual.fecha_subida ? new Date(parseFloat(manual.fecha_subida) * 1000).toLocaleDateString('es-ES') : 'N/A';
          return `
      <div class="manual-item">
        <div class="manual-info">
          <h4>${manual.nombre}</h4>
          <p>Archivo: ${manual.archivo} | Fecha: ${fecha}</p>
        </div>
        <div class="manual-actions">
          <button class="manual-btn view" onclick="abrirManual('${manual.archivo}')">
            Ver
          </button>
          <button class="manual-btn arbol" onclick="generarArbol('${manual.nombre}')">
            🌳 Generar árbol
          </button>
          <button class="manual-btn delete" onclick="confirmarEliminarManual('${manual.archivo}')">
            Eliminar
          </button>
        </div>
      </div>
    `;
        }
      )
      .join("");
  } catch (error) {
    manualesLista.innerHTML = `<p class='no-data'>Error al cargar manuales: ${error.message}</p>`;
  }
}

function abrirManual(nombreArchivo) {
  const rutaPDF = `/manuales/${nombreArchivo}`;
  window.open(rutaPDF, "_blank");
}

function confirmarEliminarManual(nombreArchivo) {
  if (confirm(`¿Estás seguro de que deseas eliminar el manual "${nombreArchivo}"?\n\nEsta acción no se puede deshacer.`)) {
    eliminarManual(nombreArchivo);
  }
}

async function eliminarManual(nombreArchivo) {
  try {
    const token = localStorage.getItem("chatbot_token");
    
    const response = await fetch(`http://127.0.0.1:8000/api/admin/manuales/${nombreArchivo}`, {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    const data = await response.json();

    if (response.ok && data.success) {
      alert(`Manual "${nombreArchivo}" eliminado correctamente`);
      // Recargar la lista
      cargarListaManuales();
    } else {
      alert(`Error al eliminar el manual: ${data.detail || 'Error desconocido'}`);
    }
  } catch (error) {
    alert(`Error al eliminar el manual: ${error.message}`);
  }
}

// -----------------------------------------
// SUBIDA DE MANUALES
// -----------------------------------------

function inicializarFormularioSubida() {
  const form = document.getElementById("upload-manual-form");
  const statusDiv = document.getElementById("upload-status");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const nombreManual = document.getElementById("manual-nombre").value.trim();
    const fileInput = document.getElementById("manual-file");
    const descripcion = document.getElementById("manual-descripcion").value.trim();
    const file = fileInput.files[0];

    if (!nombreManual) {
      mostrarEstadoSubida("error", "Por favor ingresa el nombre del manual");
      return;
    }

    if (!file) {
      mostrarEstadoSubida("error", "Por favor selecciona un archivo PDF");
      return;
    }

    if (file.type !== "application/pdf") {
      mostrarEstadoSubida("error", "Solo se permiten archivos PDF");
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      // 50MB
      mostrarEstadoSubida("error", "El archivo es demasiado grande (máximo 50MB)");
      return;
    }

    // Mostrar progreso
    mostrarEstadoSubida("info", "Subiendo archivo...");
    const uploadBtn = form.querySelector(".upload-btn");
    uploadBtn.disabled = true;

    try {
      // Crear FormData para enviar el archivo
      const formData = new FormData();
      formData.append("archivo", file);
      formData.append("nombreManual", nombreManual);

      const token = localStorage.getItem("chatbot_token");
      
      const response = await fetch("http://127.0.0.1:8000/api/admin/manuales/upload", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();

      if (response.ok && data.success) {
        mostrarEstadoSubida("success", `Manual "${nombreManual}" subido correctamente`);
        
        // Limpiar formulario
        form.reset();
        
        // Recargar lista de manuales
        setTimeout(() => {
          cargarListaManuales();
        }, 1500);
      } else {
        mostrarEstadoSubida("error", data.detail || "Error al subir el manual");
      }
    } catch (error) {
      mostrarEstadoSubida("error", `Error al subir el archivo: ${error.message}`);
    } finally {
      uploadBtn.disabled = false;
    }
  });
}

function mostrarEstadoSubida(tipo, mensaje) {
  const statusDiv = document.getElementById("upload-status");
  statusDiv.className = `upload-status ${tipo}`;
  statusDiv.textContent = mensaje;
  statusDiv.style.display = "block";
}

function getNombreAmigable(nombreTecnico) {
  const nombres = {
    hidrolavadora_karcher: "Hidrolavadora Kärcher",
    generador_generac: "Generador Generac Guardian",
    motor_cummins: "Motor Cummins",
    soldadora_miller_ranger: "Soldadora Miller Ranger 305D"
  };
  return nombres[nombreTecnico] || nombreTecnico;
}

// -----------------------------------------
// EXPORTAR ESTADÍSTICAS A PDF
// -----------------------------------------

async function exportarEstadisticasAPDF() {
  if (!estadisticasActuales) {
    alert("No hay estadisticas disponibles. Por favor, actualiza primero.");
    return;
  }

  if (typeof jspdf === 'undefined') {
    alert("Cargando libreria PDF...");
    return;
  }

  const { jsPDF } = jspdf;
  const doc = new jsPDF();
  
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  
  // Función auxiliar para agregar pie de página
  function agregarPieDePagina(pageNum, totalPages) {
    const footerY = pageHeight - 15;
    doc.setDrawColor(211, 47, 47);
    doc.setLineWidth(0.5);
    doc.line(20, footerY - 5, pageWidth - 20, footerY - 5);
    
    doc.setFontSize(8);
    doc.setTextColor(100, 100, 100);
    doc.setFont("helvetica", "italic");
    doc.text("Big Tools - Sistema Experto de Diagnóstico", 25, footerY);
    doc.text(`Página ${pageNum} de ${totalPages}`, pageWidth - 25, footerY, { align: 'right' });
  }
  
  // Obtener usuario actual
  const usuarioActual = localStorage.getItem('chatbot_username') || 'admin';
  
  // ========== ENCABEZADO MODERNO ==========
  doc.setFillColor(52, 73, 94);
  doc.rect(0, 0, pageWidth, 35, 'F');
  
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(22);
  doc.setFont("helvetica", "bold");
  doc.text("BIG TOOLS", pageWidth / 2, 15, { align: 'center' });
  
  doc.setFontSize(12);
  doc.setFont("helvetica", "normal");
  doc.text("Reporte de Estadísticas del Sistema", pageWidth / 2, 25, { align: 'center' });
  
  doc.setDrawColor(211, 47, 47);
  doc.setLineWidth(1);
  doc.line(33, 30, pageWidth - 33, 30);
  
  let y = 40;

  // Fecha y usuario en el encabezado
  doc.setFontSize(9);
  doc.setTextColor(100, 100, 100);
  doc.setFont("helvetica", "normal");
  const now = new Date();
  const fecha = `${now.getDate()} de ${now.toLocaleString('es-ES', { month: 'long' })} de ${now.getFullYear()}, ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
  doc.text(`Fecha de generación: ${fecha}`, 25, y);
  doc.text(`Usuario: ${usuarioActual}`, pageWidth - 25, y, { align: 'right' });
  
  y = 55;

  // ========== RESUMEN GENERAL ==========
  doc.setFillColor(211, 47, 47);
  doc.rect(20, y, pageWidth - 40, 8, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("RESUMEN GENERAL", 25, y + 5.5);
  
  y += 15;
  doc.setTextColor(0, 0, 0);
  doc.setFontSize(12);
  doc.setFont("helvetica", "bold");
  doc.text(`Total de Diagnósticos: ${estadisticasActuales.total_diagnosticos || 0}`, 25, y);
  y += 12;

  // ========== MÁQUINAS MÁS CONSULTADAS ==========
  doc.setFillColor(211, 47, 47);
  doc.rect(20, y, pageWidth - 40, 8, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("MÁQUINAS MÁS CONSULTADAS", 25, y + 5.5);
  
  y += 15;
  doc.setTextColor(0, 0, 0);
  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  
  if (estadisticasActuales.top_maquinas && estadisticasActuales.top_maquinas.length > 0) {
    estadisticasActuales.top_maquinas.forEach((item, index) => {
      if (y > pageHeight - 30) {
        doc.addPage();
        y = 45;
      }
      doc.setFont("helvetica", "bold");
      doc.text(`${index + 1}.`, 25, y);
      doc.setFont("helvetica", "normal");
      doc.text(`${item.maquina}:`, 32, y);
      doc.setFont("helvetica", "bold");
      doc.setTextColor(211, 47, 47);
      doc.text(`${item.cantidad} consultas`, 140, y);
      doc.setTextColor(0, 0, 0);
      y += 6;
    });
  } else {
    doc.text("No hay datos disponibles", 25, y);
    y += 6;
  }
  y += 8;

  // ========== CATEGORÍAS MÁS CONSULTADAS ==========
  doc.setFillColor(211, 47, 47);
  doc.rect(20, y, pageWidth - 40, 8, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("CATEGORÍAS MÁS CONSULTADAS", 25, y + 5.5);
  
  y += 15;
  doc.setTextColor(0, 0, 0);
  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  
  if (estadisticasActuales.top_categorias && estadisticasActuales.top_categorias.length > 0) {
    estadisticasActuales.top_categorias.forEach((item, index) => {
      if (y > pageHeight - 30) {
        doc.addPage();
        y = 45;
      }
      const categoriaTexto = `${index + 1}. ${item.categoria}:`;
      const lineas = doc.splitTextToSize(categoriaTexto, pageWidth - 100);
      doc.setFont("helvetica", "normal");
      doc.text(lineas[0], 25, y);
      doc.setFont("helvetica", "bold");
      doc.setTextColor(211, 47, 47);
      doc.text(`${item.cantidad} consultas`, 140, y);
      doc.setTextColor(0, 0, 0);
      y += 6;
    });
  } else {
    doc.text("No hay datos disponibles", 25, y);
    y += 6;
  }
  y += 8;

  // Verificar si necesitamos nueva página para el historial
  if (y > pageHeight - 80) {
    doc.addPage();
    y = 45;
  }

  // ========== HISTORIAL RECIENTE ==========
  doc.setFillColor(211, 47, 47);
  doc.rect(20, y, pageWidth - 40, 8, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text("HISTORIAL RECIENTE (ÚLTIMOS 20 REGISTROS)", 25, y + 5.5);
  
  y += 15;
  doc.setTextColor(0, 0, 0);
  doc.setFontSize(9);
  
  if (estadisticasActuales.historial_reciente && estadisticasActuales.historial_reciente.length > 0) {
    // Encabezados de tabla con fondo gris
    doc.setFillColor(240, 240, 240);
    doc.rect(20, y - 4, pageWidth - 40, 7, 'F');
    
    doc.setFont("helvetica", "bold");
    doc.setTextColor(0, 0, 0);
    doc.text("Fecha", 25, y);
    doc.text("Máquina", 65, y);
    doc.text("Categoría", 130, y);
    y += 8;
    doc.setFont("helvetica", "normal");

    // Línea debajo de encabezados
    doc.setDrawColor(211, 47, 47);
    doc.setLineWidth(0.5);
    doc.line(20, y - 3, pageWidth - 20, y - 3);

    // Filas de datos con líneas alternas
    let isAlternate = false;
    estadisticasActuales.historial_reciente.slice(0, 20).forEach((item) => {
      if (y > pageHeight - 30) {
        doc.addPage();
        y = 45;
      }

      // Fondo alternado
      if (isAlternate) {
        doc.setFillColor(250, 250, 250);
        doc.rect(20, y - 4, pageWidth - 40, 6, 'F');
      }
      isAlternate = !isAlternate;

      const fechaObj = new Date(item.timestamp);
      const fechaFormato = fechaObj.toLocaleDateString('es-ES', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

      doc.setTextColor(0, 0, 0);
      doc.text(fechaFormato, 25, y);
      
      const maquinaTexto = doc.splitTextToSize(item.maquina || "N/A", 60);
      doc.text(maquinaTexto[0], 65, y);
      
      const categoriaTexto = doc.splitTextToSize(item.categoria || "N/A", 55);
      doc.text(categoriaTexto[0], 130, y);
      
      y += 6;
    });
  } else {
    doc.text("No hay historial disponible", 25, y);
  }

  // Agregar pie de página a todas las páginas
  const totalPages = doc.internal.pages.length - 1;
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    agregarPieDePagina(i, totalPages);
  }

  // Guardar el PDF
  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const nombreArchivo = `BigTools_Estadisticas_${timestamp}.pdf`;
  doc.save(nombreArchivo);
}

// -----------------------------------------
// EXPORTAR ESTADÍSTICAS A CSV
// -----------------------------------------

function exportarEstadisticasACSV() {
  if (!estadisticasActuales) {
    alert("No hay estadisticas disponibles. Por favor, actualiza primero.");
    return;
  }

  try {
    let csvContent = "";

    // Encabezado del CSV
    csvContent += "REPORTE DE ESTADISTICAS - BIG TOOLS\n";
    csvContent += `Fecha de Generacion: ${new Date().toLocaleString('es-ES')}\n\n`;

    // Total de diagnósticos
    csvContent += "RESUMEN GENERAL\n";
    csvContent += `Total de Diagnosticos,${estadisticasActuales.total_diagnosticos || 0}\n\n`;

    // Top Máquinas
    csvContent += "MAQUINAS MAS CONSULTADAS\n";
    csvContent += "Posicion,Maquina,Cantidad de Consultas\n";
    if (estadisticasActuales.top_maquinas && estadisticasActuales.top_maquinas.length > 0) {
      estadisticasActuales.top_maquinas.forEach((item, index) => {
        csvContent += `${index + 1},"${item.maquina}",${item.cantidad}\n`;
      });
    } else {
      csvContent += "No hay datos disponibles\n";
    }
    csvContent += "\n";

    // Top Categorías
    csvContent += "CATEGORIAS MAS CONSULTADAS\n";
    csvContent += "Posicion,Categoria,Cantidad de Consultas\n";
    if (estadisticasActuales.top_categorias && estadisticasActuales.top_categorias.length > 0) {
      estadisticasActuales.top_categorias.forEach((item, index) => {
        csvContent += `${index + 1},"${item.categoria}",${item.cantidad}\n`;
      });
    } else {
      csvContent += "No hay datos disponibles\n";
    }
    csvContent += "\n";

    // Historial Reciente
    csvContent += "HISTORIAL RECIENTE\n";
    csvContent += "Fecha y Hora,Maquina,Categoria\n";
    if (estadisticasActuales.historial_reciente && estadisticasActuales.historial_reciente.length > 0) {
      estadisticasActuales.historial_reciente.forEach((item) => {
        const fechaObj = new Date(item.timestamp);
        const fechaFormato = fechaObj.toLocaleString('es-ES');
        csvContent += `"${fechaFormato}","${item.maquina || 'N/A'}","${item.categoria || 'N/A'}"\n`;
      });
    } else {
      csvContent += "No hay historial disponible\n";
    }

    // Crear archivo CSV y descargar
    const blob = new Blob(["\ufeff" + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    const nombreArchivo = `estadisticas_bigtools_${Date.now()}.csv`;

    link.setAttribute("href", url);
    link.setAttribute("download", nombreArchivo);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

  } catch (error) {
    alert("Error al exportar a CSV. Intenta de nuevo.");
  }
}

// -----------------------------------------
// TOOLTIP DE EXPORTACIÓN (PDF/CSV)
// -----------------------------------------

const exportButton = document.getElementById("export-button");
const exportTooltip = document.getElementById("export-tooltip");
const tooltipOptions = document.querySelectorAll(".tooltip-option");

// Mostrar/ocultar tooltip al hacer clic en el botón
if (exportButton && exportTooltip) {
  exportButton.addEventListener("click", (e) => {
    e.stopPropagation();
    
    if (!estadisticasActuales) {
      alert("No hay estadisticas disponibles. Por favor, actualiza primero.");
      return;
    }
    
    exportTooltip.classList.toggle("show");
  });

  // Cerrar tooltip al hacer clic fuera
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".export-wrapper")) {
      exportTooltip.classList.remove("show");
    }
  });
}

// Manejar las opciones del tooltip
tooltipOptions.forEach(option => {
  option.addEventListener("click", (e) => {
    e.stopPropagation();
    const formato = option.getAttribute("data-format");
    exportTooltip.classList.remove("show");

    if (formato === "pdf") {
      exportarEstadisticasAPDF();
    } else if (formato === "csv") {
      exportarEstadisticasACSV();
    }
  });
});

// -----------------------------------------
// GESTIÓN RAG
// -----------------------------------------

// Polling activo por máquina: { [nombreMaquina]: intervalId }
const _ragPolling = {};

async function cargarEstadoRAG() {
  const lista = document.getElementById("rag-manuales-lista");
  if (!lista) return;
  lista.innerHTML = "<p class='loading'>Cargando estado RAG...</p>";

  try {
    const response = await fetch(`${API_URL}/rag/estado`);
    if (!response.ok) throw new Error("Error al obtener estado RAG");
    const data = await response.json();
    renderizarListaRAG(data.manuales || []);
  } catch (err) {
    lista.innerHTML = `<p class='no-data'>❌ Error: ${err.message}</p>`;
  }
}

function renderizarListaRAG(manuales) {
  const lista = document.getElementById("rag-manuales-lista");
  if (!lista) return;

  if (manuales.length === 0) {
    lista.innerHTML = "<p class='no-data'>No hay manuales disponibles.</p>";
    return;
  }

  lista.innerHTML = manuales.map(m => {
    const badge = m.indexado
      ? `<span class="rag-badge indexado">✓ Indexado</span>`
      : `<span class="rag-badge no-indexado">✗ No indexado</span>`;

    const btnText = m.indexado ? "Re-indexar" : "Indexar";

    return `
      <div class="manual-item" id="rag-item-${_ragId(m.nombre)}">
        <div class="manual-info">
          <h4>${m.nombre} ${badge}</h4>
          <div class="rag-progress-wrapper" id="rag-progress-${_ragId(m.nombre)}">
            <div class="rag-progress-track">
              <div class="rag-progress-fill" id="rag-fill-${_ragId(m.nombre)}"></div>
            </div>
            <div class="rag-progress-meta">
              <span id="rag-pct-${_ragId(m.nombre)}">0%</span>
              <span id="rag-eta-${_ragId(m.nombre)}"></span>
            </div>
            <div class="rag-progress-msg" id="rag-msg-${_ragId(m.nombre)}"></div>
          </div>
        </div>
        <div class="manual-actions">
          <button
            class="rag-indexar-btn"
            id="rag-btn-${_ragId(m.nombre)}"
            onclick="iniciarIndexacionRAG('${m.nombre}')">
            ${btnText}
          </button>
        </div>
      </div>`;
  }).join("");
}

function _ragId(nombre) {
  // Convierte el nombre en un ID CSS seguro
  return nombre.toLowerCase().replace(/[^a-z0-9]/g, "_");
}

async function iniciarIndexacionRAG(nombreMaquina) {
  const id  = _ragId(nombreMaquina);
  const btn = document.getElementById(`rag-btn-${id}`);

  btn.disabled  = true;
  btn.textContent = "Iniciando...";

  try {
    const response = await fetch(`${API_URL}/rag/indexar/${encodeURIComponent(nombreMaquina)}`, {
      method: "POST",
    });

    if (response.status === 409) {
      btn.textContent = "En curso...";
    } else if (!response.ok) {
      const err = await response.json();
      alert(`Error al iniciar indexación: ${err.detail}`);
      btn.disabled    = false;
      btn.textContent = "Indexar";
      return;
    }

    // Mostrar barra de progreso y comenzar polling
    const progressEl = document.getElementById(`rag-progress-${id}`);
    if (progressEl) progressEl.classList.add("visible");
    btn.textContent = "Indexando...";

    _iniciarPollingProgreso(nombreMaquina);

  } catch (err) {
    alert(`Error de conexión: ${err.message}`);
    btn.disabled    = false;
    btn.textContent = "Indexar";
  }
}

function _iniciarPollingProgreso(nombreMaquina) {
  const id = _ragId(nombreMaquina);

  // Evitar doble polling
  if (_ragPolling[nombreMaquina]) {
    clearInterval(_ragPolling[nombreMaquina]);
  }

  _ragPolling[nombreMaquina] = setInterval(async () => {
    try {
      const res   = await fetch(`${API_URL}/rag/progreso/${encodeURIComponent(nombreMaquina)}`);
      const datos = await res.json();

      _actualizarBarraProgreso(id, datos);

      if (datos.estado === "completado" || datos.estado === "error") {
        clearInterval(_ragPolling[nombreMaquina]);
        delete _ragPolling[nombreMaquina];

        const btn = document.getElementById(`rag-btn-${id}`);
        if (btn) {
          btn.disabled    = false;
          btn.textContent = datos.estado === "completado" ? "Re-indexar" : "Reintentar";
        }

        // Recargar lista completa para actualizar el badge
        if (datos.estado === "completado") {
          setTimeout(cargarEstadoRAG, 800);
        }
      }
    } catch (_) {
      // ignorar errores de red transitorios
    }
  }, 800);
}

function _actualizarBarraProgreso(id, datos) {
  const fill  = document.getElementById(`rag-fill-${id}`);
  const pct   = document.getElementById(`rag-pct-${id}`);
  const eta   = document.getElementById(`rag-eta-${id}`);
  const msg   = document.getElementById(`rag-msg-${id}`);

  if (!fill) return;

  const porcentaje = datos.porcentaje || 0;
  fill.style.width = `${porcentaje}%`;

  // Color de la barra según estado
  fill.classList.remove("completado", "error");
  if (datos.estado === "completado") fill.classList.add("completado");
  if (datos.estado === "error")      fill.classList.add("error");

  if (pct) pct.textContent = `${porcentaje}%`;

  if (eta) {
    if (datos.segundos_restantes !== null && datos.segundos_restantes > 0) {
      const mins = Math.floor(datos.segundos_restantes / 60);
      const segs = datos.segundos_restantes % 60;
      eta.textContent = mins > 0
        ? `~${mins}m ${segs}s restantes`
        : `~${segs}s restantes`;
    } else if (datos.estado === "completado") {
      eta.textContent = "✓ Completado";
    } else {
      eta.textContent = "";
    }
  }

  if (msg) msg.textContent = datos.mensaje || "";
}

// Botón "Actualizar" del tab RAG
document.addEventListener("DOMContentLoaded", () => {
  const refreshRAG = document.getElementById("rag-refresh-btn");
  if (refreshRAG) {
    refreshRAG.addEventListener("click", cargarEstadoRAG);
  }
});

// -----------------------------------------
// DEBUG RAG
// -----------------------------------------

async function cargarMaquinasDebug() {
  const select = document.getElementById("debug-maquina");
  if (!select) return;

  try {
    const res  = await fetch(`${API_URL}/rag/estado`);
    const data = await res.json();
    const manuales = (data.manuales || []).filter(m => m.indexado);

    // Limpiar y repoblar
    select.innerHTML = '<option value="">— Seleccioná una máquina —</option>';
    manuales.forEach(m => {
      const opt = document.createElement("option");
      opt.value       = m.nombre;
      opt.textContent = m.nombre;
      select.appendChild(opt);
    });

    if (manuales.length === 0) {
      const opt = document.createElement("option");
      opt.value       = "";
      opt.textContent = "(No hay manuales indexados)";
      opt.disabled    = true;
      select.appendChild(opt);
    }
  } catch (err) {
    console.error("No se pudo cargar lista de máquinas para debug:", err);
  }
}

async function ejecutarDebugChunks() {
  const maquina = document.getElementById("debug-maquina").value.trim();
  const query   = document.getElementById("debug-query").value.trim();
  const card    = document.getElementById("debug-resultados-card");
  const titulo  = document.getElementById("debug-resultados-titulo");
  const body    = document.getElementById("debug-resultados-body");
  const btn     = document.getElementById("debug-buscar-btn");

  if (!maquina) { alert("Seleccioná una máquina primero."); return; }
  if (!query)   { alert("Ingresá una consulta."); return; }

  btn.disabled     = true;
  btn.textContent  = "Buscando...";
  card.style.display = "block";
  titulo.textContent = "Buscando…";
  body.innerHTML   = "<p class='loading'>Consultando el sistema RAG...</p>";

  try {
    const res = await fetch(`${API_URL}/rag/debug/chunks`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ nombre_maquina: maquina, pregunta: query }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    titulo.textContent = `Resultados para "${query}" — ${data.total} chunk(s) recuperado(s)`;

    if (!data.chunks || data.chunks.length === 0) {
      body.innerHTML = "<p class='no-data'>⚠️ No se recuperó ningún chunk. El manual puede no estar indexado o la consulta no tiene coincidencias.</p>";
      return;
    }

    // Tabla de resultados
    const filas = data.chunks.map((c, i) => {
      const scoreColor = c.score >= 0.5 ? "#388e3c" : c.score >= 0.3 ? "#f57c00" : "#d32f2f";
      const idiomaIcon = c.idioma === "es" ? "🇦🇷" : c.idioma === "en" ? "🇺🇸" : "❓";
      const textoEscapado = c.texto
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

      return `
        <tr style="border-bottom:1px solid #eee;">
          <td style="padding:8px 6px;text-align:center;font-weight:bold;">${i + 1}</td>
          <td style="padding:8px 6px;text-align:center;">${c.pagina}</td>
          <td style="padding:8px 6px;text-align:center;font-weight:bold;color:${scoreColor};">${c.score.toFixed(3)}</td>
          <td style="padding:8px 6px;text-align:center;">${idiomaIcon} ${c.idioma}</td>
          <td style="padding:8px 6px;font-size:0.8rem;color:#555;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${c.seccion}">${c.seccion || "—"}</td>
          <td style="padding:8px 6px;font-size:0.82rem;max-width:360px;">
            <details>
              <summary style="cursor:pointer;color:#1976d2;">${textoEscapado.slice(0, 80)}…</summary>
              <pre style="white-space:pre-wrap;margin-top:6px;background:#f5f5f5;padding:8px;border-radius:4px;font-size:0.78rem;">${textoEscapado}</pre>
            </details>
          </td>
        </tr>`;
    }).join("");

    body.innerHTML = `
      <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
        <thead>
          <tr style="background:#f5f5f5;text-align:left;">
            <th style="padding:8px 6px;">#</th>
            <th style="padding:8px 6px;">Pág.</th>
            <th style="padding:8px 6px;">Score</th>
            <th style="padding:8px 6px;">Idioma</th>
            <th style="padding:8px 6px;">Sección</th>
            <th style="padding:8px 6px;">Texto (click para expandir)</th>
          </tr>
        </thead>
        <tbody>${filas}</tbody>
      </table>
      <p style="margin-top:10px;font-size:0.8rem;color:#888;">
        Score ≥ 0.5 🟢 relevante &nbsp;|&nbsp; 0.3–0.5 🟠 marginal &nbsp;|&nbsp; &lt;0.3 🔴 poco relevante
      </p>`;

  } catch (err) {
    body.innerHTML = `<p class='no-data'>❌ Error: ${err.message}</p>`;
  } finally {
    btn.disabled    = false;
    btn.textContent = "Buscar chunks";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("debug-buscar-btn");
  if (btn) btn.addEventListener("click", ejecutarDebugChunks);

  // También disparar con Enter en el input
  const input = document.getElementById("debug-query");
  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") ejecutarDebugChunks();
    });
  }
});

// -----------------------------------------
// INICIALIZACIÓN
// -----------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  verificarSesion();
  inicializarPestanas();
  inicializarFormularioSubida();
});

// -----------------------------------------
// GENERACIÓN AUTOMÁTICA DE ÁRBOL (borrador) + VALIDACIÓN
// -----------------------------------------

let _arbolMaquinaActual = null;

let _arbolPoll = null;

async function generarArbol(nombre) {
  const token = localStorage.getItem("chatbot_token");
  _arbolMaquinaActual = nombre;
  document.getElementById("arbol-titulo").textContent = "Generar árbol — " + nombre;
  document.getElementById("arbol-json").value = "";
  document.getElementById("arbol-progreso-wrap").style.display = "block";
  _arbolSetProgreso(0, "Iniciando… (esto puede tardar varios minutos)", null);
  document.getElementById("arbol-modal").style.display = "flex";
  try {
    const r = await fetch(`${API_URL}/admin/arbol/generar/${encodeURIComponent(nombre)}`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` },
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Error al iniciar");
    _arbolPollProgreso(nombre);
  } catch (e) {
    document.getElementById("arbol-msg").textContent = "Error: " + e.message;
  }
}

function _arbolSetProgreso(pct, texto, seg) {
  const bar = document.getElementById("arbol-bar");
  if (bar) bar.style.width = (pct || 0) + "%";
  let t = texto || "";
  if (seg != null && seg > 0) {
    const m = Math.floor(seg / 60), s = seg % 60;
    t += m > 0 ? `  (~${m}m ${s}s restantes)` : `  (~${s}s restantes)`;
  }
  document.getElementById("arbol-msg").textContent = t;
}

function _arbolPollProgreso(nombre) {
  const token = localStorage.getItem("chatbot_token");
  clearInterval(_arbolPoll);
  _arbolPoll = setInterval(async () => {
    try {
      const r = await fetch(`${API_URL}/admin/arbol/progreso/${encodeURIComponent(nombre)}`, {
        headers: { "Authorization": `Bearer ${token}` },
      });
      const p = await r.json();
      _arbolSetProgreso(p.porcentaje, p.mensaje, p.segundos_restantes);
      if (p.estado === "completado") {
        clearInterval(_arbolPoll);
        document.getElementById("arbol-progreso-wrap").style.display = "none";
        document.getElementById("arbol-json").value =
          JSON.stringify({ categorias: (p.arbol && p.arbol.categorias) || [] }, null, 2);
      } else if (p.estado === "error") {
        clearInterval(_arbolPoll);
        document.getElementById("arbol-progreso-wrap").style.display = "none";
        document.getElementById("arbol-msg").textContent = p.mensaje || "Error";
      }
    } catch (e) { /* reintentar */ }
  }, 1500);
}

async function aprobarArbol() {
  const token = localStorage.getItem("chatbot_token");
  const ta = document.getElementById("arbol-json");
  const msg = document.getElementById("arbol-msg");
  let arbol;
  try {
    arbol = JSON.parse(ta.value);
  } catch (e) {
    msg.textContent = "⚠️ El JSON tiene un error de formato: " + e.message;
    return;
  }
  if (!arbol.categorias || !Array.isArray(arbol.categorias)) {
    msg.textContent = "⚠️ El JSON debe tener una lista 'categorias'.";
    return;
  }
  try {
    const r = await fetch(`${API_URL}/admin/arbol/aprobar/${encodeURIComponent(_arbolMaquinaActual)}`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ categorias: arbol.categorias }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Error al aprobar");
    msg.textContent = "✅ " + data.mensaje;
    setTimeout(cerrarModalArbol, 1400);
  } catch (e) {
    msg.textContent = "Error al aprobar: " + e.message;
  }
}

function cerrarModalArbol() {
  clearInterval(_arbolPoll);
  document.getElementById("arbol-modal").style.display = "none";
}


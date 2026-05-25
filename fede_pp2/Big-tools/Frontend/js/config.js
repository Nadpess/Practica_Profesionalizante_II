/**
 * Configuración de la API
 * 
 * Esta configuración detecta automáticamente la URL del servidor desde el que
 * se está sirviendo la página. No necesitas cambiar nada manualmente.
 * 
 * Si necesitas usar un servidor diferente (ej: API en otro puerto o dominio),
 * descomenta y modifica la línea API_BASE_URL_MANUAL abajo.
 */

// ========== CONFIGURACIÓN DE LA API ==========

(function() {
    'use strict';
    
    // Detectar automáticamente la URL del servidor actual
    // Esto funciona cuando el frontend se sirve desde el backend
    var API_BASE_URL = window.location.origin || "http://127.0.0.1:8000";
    
    // Si necesitas usar un servidor de API diferente, descomenta y configura esto:
    // var API_BASE_URL_MANUAL = "http://192.168.1.100:8000";
    // API_BASE_URL = API_BASE_URL_MANUAL;
    
    // Hacer las variables globales
    window.API_BASE_URL = API_BASE_URL;
    window.API_URL = API_BASE_URL + "/api";
    
    // Exportar para uso en otros archivos (si es necesario)
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { API_URL: window.API_URL, API_BASE_URL: window.API_BASE_URL };
    }
})();


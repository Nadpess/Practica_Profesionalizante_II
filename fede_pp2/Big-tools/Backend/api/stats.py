"""
stats.py
Módulo para rastrear y gestionar estadísticas del sistema experto.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

STATS_FILE = Path(__file__).parent.parent / "data" / "stats.json"

class StatsManager:
    """
    Gestiona las estadísticas del sistema de diagnóstico.
    """
    
    def __init__(self):
        self.stats = self._cargar_stats()
    
    def _cargar_stats(self) -> dict:
        """Carga las estadísticas desde el archivo JSON."""
        defaults = {
            "total_diagnosticos": 0,
            "diagnosticos_por_maquina": {},
            "diagnosticos_por_categoria": {},
            "historial": [],
            # ── RAG ──────────────────────────────
            "total_consultas_rag": 0,
            "consultas_rag_por_maquina": {},
        }

        if not STATS_FILE.exists():
            return defaults

        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Retrocompatibilidad: agregar claves RAG si no existen
            for key, val in defaults.items():
                data.setdefault(key, val)
            return data
        except Exception:
            return defaults
    
    def _guardar_stats(self):
        """Guarda las estadísticas en el archivo JSON."""
        try:
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar estadísticas: {e}")
    
    def registrar_diagnostico_iniciado(self, maquina: str, categoria: str):
        """
        Registra el inicio de un diagnóstico.
        """
        self.stats["total_diagnosticos"] += 1
        
        # Contador por máquina
        if maquina not in self.stats["diagnosticos_por_maquina"]:
            self.stats["diagnosticos_por_maquina"][maquina] = 0
        self.stats["diagnosticos_por_maquina"][maquina] += 1
        
        # Contador por categoría
        categoria_key = f"{maquina}|{categoria}"
        if categoria_key not in self.stats["diagnosticos_por_categoria"]:
            self.stats["diagnosticos_por_categoria"][categoria_key] = 0
        self.stats["diagnosticos_por_categoria"][categoria_key] += 1
        
        # Agregar al historial
        self.stats["historial"].append({
            "timestamp": datetime.now().isoformat(),
            "maquina": maquina,
            "categoria": categoria,
            "completado": False
        })
        
        # Mantener solo los últimos 50 registros
        if len(self.stats["historial"]) > 50:
            self.stats["historial"] = self.stats["historial"][-50:]
        
        self._guardar_stats()
    
    def registrar_consulta_rag(self, maquina: str, pregunta: str):
        """Registra una consulta RAG."""
        self.stats["total_consultas_rag"] = self.stats.get("total_consultas_rag", 0) + 1

        if maquina not in self.stats.get("consultas_rag_por_maquina", {}):
            self.stats.setdefault("consultas_rag_por_maquina", {})[maquina] = 0
        self.stats["consultas_rag_por_maquina"][maquina] += 1

        self._guardar_stats()

    def registrar_diagnostico_completado(self, maquina: str, categoria: str, falla: str):
        """
        Marca un diagnóstico como completado.
        """
        # Buscar el último diagnóstico no completado para esta máquina/categoría
        for entry in reversed(self.stats["historial"]):
            if (entry["maquina"] == maquina and 
                entry["categoria"] == categoria and 
                not entry.get("completado", False)):
                entry["completado"] = True
                entry["falla"] = falla
                break
        
        self._guardar_stats()
    
    def obtener_estadisticas(self) -> dict:
        """
        Retorna un resumen de las estadísticas.
        """
        # Top 3 máquinas más consultadas
        maquinas_ordenadas = sorted(
            self.stats["diagnosticos_por_maquina"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # Top 5 categorías más consultadas
        categorias_ordenadas = sorted(
            self.stats["diagnosticos_por_categoria"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Últimos 10 diagnósticos
        historial_reciente = self.stats["historial"][-10:]
        historial_reciente.reverse()
        
        # Top 3 máquinas más consultadas en RAG
        rag_maquinas_ordenadas = sorted(
            self.stats.get("consultas_rag_por_maquina", {}).items(),
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        return {
            "total_diagnosticos":   self.stats["total_diagnosticos"],
            "top_maquinas":         [{"maquina": m, "cantidad": c} for m, c in maquinas_ordenadas],
            "top_categorias":       [
                {"categoria": c.split("|")[1], "maquina": c.split("|")[0], "cantidad": cant}
                for c, cant in categorias_ordenadas
            ],
            "historial_reciente":   historial_reciente,
            # ── RAG ──────────────────────────────────────────────────────────
            "total_consultas_rag":  self.stats.get("total_consultas_rag", 0),
            "top_maquinas_rag":     [{"maquina": m, "cantidad": c} for m, c in rag_maquinas_ordenadas],
        }

# Instancia global para uso en las rutas
stats_manager = StatsManager()


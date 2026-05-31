# Big Tools — Requisitos para instalar y correr

Big Tools funciona **100% en la computadora del cliente** (offline). Toda la inteligencia
artificial corre localmente: una vez instalado y descargados los modelos, **no necesita
internet** y ningún dato sale de la empresa.

---

## Software necesario

| Componente | Detalle |
|---|---|
| Sistema operativo | Windows 10 u 11 (64 bits) |
| Ollama | Motor que corre la IA local — se descarga de ollama.com |
| Modelos de IA | `qwen3:4b` (responde el diagnóstico) y `nomic-embed-text` (busca en los manuales) |
| Python | Versión 3.10 o superior |

---

## Hardware

### Mínimo (funciona, más lento — solo CPU)

- Procesador de 4 núcleos moderno (Intel Core i5 / AMD Ryzen 5, de los últimos años).
- **8 GB de RAM** (16 GB recomendado).
- **15 GB de disco libre** (idealmente SSD) para los modelos y los manuales.
- Sin placa de video dedicada: funciona, pero las respuestas tardan más (varios segundos).

### Recomendado (respuestas rápidas y fluidas)

- Procesador reciente de 6+ núcleos.
- **16 GB de RAM.**
- **Placa de video NVIDIA con 6–8 GB de memoria (VRAM)** o más.
- Disco **SSD** con 15–20 GB libres.

---

## Sobre la placa de video (importante para la velocidad)

La velocidad de respuesta depende **sobre todo de la placa de video**:

- **Con placa NVIDIA**: Ollama la usa automáticamente y las respuestas son varias veces más rápidas.
  - 4 GB de VRAM (ej. GTX 1650): funciona bien.
  - 6–8 GB o más: ideal, deja margen para crecer o usar un modelo más potente.
- **Sin placa NVIDIA (solo procesador)**: funciona igual, pero más lento (las respuestas
  se escriben de a poco, a unos pocos segundos por respuesta).

> En resumen: anda en una PC común; con una placa NVIDIA va notablemente más rápido.

---

## Instalación (resumen de pasos)

1. Instalar **Ollama** (desde ollama.com).
2. Descargar los modelos (una sola vez, con internet):
   ```
   ollama pull qwen3:4b
   ollama pull nomic-embed-text
   ```
3. Instalar **Python 3.10+**.
4. Instalar las dependencias del proyecto (`pip install -r requirements.txt`).
5. Iniciar el programa (backend) y abrir el navegador en la dirección local indicada.

Después del paso 2, **el sistema ya no necesita internet** para funcionar.

---

## Notas

- El espacio en disco crece a medida que se cargan más manuales (cada manual indexado
  ocupa unos pocos MB).
- Si en el futuro se quiere más calidad de respuesta y la PC tiene una buena placa de
  video, se puede cambiar a un modelo más grande **cambiando una sola línea de
  configuración** (el sistema ya está preparado para eso).

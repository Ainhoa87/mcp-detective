# Respuestas — Deber 5: MCP Detective

## 1. Arquitectura
* **Qué hizo el LLM (Codex):** Interpretó las instrucciones del usuario, decidió cuándo y qué herramientas invocar, y estructuró las respuestas en lenguaje natural a partir de los datos devueltos.
* **Qué hizo el harness/host (VS Code / Codex Chat):** Actuó como cliente MCP, gestionó la interfaz de chat y puenteó las llamadas del modelo hacia el proceso del servidor.
* **Qué hizo el cliente MCP:** Estableció la comunicación estructurada mediante el protocolo de transporte.
* **Qué hizo el servidor MCP (`server.py`):** Ejecutó la lógica de negocio real, leyendo el archivo `casos.json` y manejando las herramientas de memoria.
* **Quién ejecutó realmente Python:** El intérprete local configurado en el entorno virtual (`.venv/Scripts/python.exe`), activado por el proceso hijo a través de `stdio`.

## 2. Evidencia (INC-003)
* INC-003 muestra cuatro intentos fallidos seguidos de un acceso exitoso (`LOGIN_SUCCESS`) para el usuario `admin` desde la IP `192.0.2.50` en el panel de administración. 
* Esto merece investigación por la secuencia anómala de fallos previos, pero **no confirma una intrusión** porque podría tratarse de un usuario legítimo que olvidó su contraseña varias veces antes de recordarla e iniciar sesión correctamente.

## 3. Validación y seguridad (`INC-999` y parámetros)
* **Quién rechaza `INC-999`:** La lógica interna del servidor Python (`server.py`) al no encontrar el identificador en los datos.
* **Por qué no es seguro confiar solo en el modelo:** Los LLM son probabilísticos y podrían alucinar datos, omitir restricciones o inventar eventos si no existe una validación estricta y determinista en el backend del servidor.

## Configuración y ejecución
* **Agente utilizado:** GitHub Codex.
* **Cómo se comprobó la conexión:** Mediante el descubrimiento dinámico de herramientas y las trazas de ejecución en la interfaz de Codex.
* **Pasos de instalación y arranque:**
  1. Clonar el repositorio y abrirlo en VS Code.
  2. Configurar el entorno virtual e instalar las dependencias de MCP.
  3. Registrar la ruta del servidor en la configuración local de VS Code (`.vscode/mcp.json`).
  4. Iniciar la sesión con el agente Codex para activar el transporte por `stdio` e invocar las herramientas de análisis.
# HomeBot

Tu propio bot de IA en tu PC con Windows: lo llamas con **Windows + Y**, le hablas, y te responde con texto y voz.
Usa [Hermes Agent](https://github.com/NousResearch/hermes-agent) con el modelo **DeepSeek** (pagas solo los tokens que gastes, con tu propia API key).

## Instalar (Windows 10/11)

1. Consigue una API key en <https://platform.deepseek.com/api_keys> y recarga saldo (con poco alcanza para muchísimos mensajes).
2. Descarga este proyecto (botón verde **Code → Download ZIP**) y descomprímelo.
3. Clic derecho en `instalar.ps1` → **Ejecutar con PowerShell**.
   Si Windows se queja de permisos: abre PowerShell en la carpeta y ejecuta
   `powershell -ExecutionPolicy Bypass -File .\instalar.ps1`
4. Responde las preguntas (nombre del bot, tu nombre, tono) y pega tu API key.

El instalador revisa qué le falta a tu PC (Python, Hermes y los paquetes de `requirements.txt`), lo descarga solo y deja HomeBot arrancando con Windows.

## Usarlo

| Atajo | Qué hace |
|---|---|
| **Windows + Y** | Empieza a grabar. Otra vez para enviar. |
| **Windows + Shift + Y** | Escribirle en una cajita. |
| **Windows + Ctrl + Y** | Cortar la voz o cancelar. |

La respuesta aparece abajo a la derecha (clic para cerrarla) y se lee en voz alta.

## Cambiar cosas

- **Otra API key:** ejecuta `cambiar-clave.ps1`. La clave queda solo en tu PC (nunca en este repositorio).
- **Otra voz:** variable de entorno `HOMEBOT_VOZ`, por ejemplo `es-PE-CamilaNeural`, `es-MX-JorgeNeural`, `es-ES-AlvaroNeural`.
- **Personalidad:** edita el `SOUL.md` de tu perfil (la ruta sale con `hermes -p homebot config path`) o vuelve a ejecutar `instalar.ps1`.
- **Quitarlo:** `desinstalar.ps1`.
- **Probar sin micrófono:** `.venv\Scripts\python.exe homebot.py --texto "hola"`.

## Seguridad

- El bot **no tiene terminal, ni acceso a archivos, ni navegador de control**: solo conversa y busca en la web. Aun así, no le pegues contraseñas ni datos sensibles.
- Tus conversaciones y tu clave quedan guardadas en tu PC (carpeta de Hermes). **No lo instales en una PC pública o compartida.**
- Cada mensaje gasta tokens de tu cuenta de DeepSeek.
- Los atajos globales leen el teclado solo para detectar esas combinaciones; el código está en `homebot.py` (corto, revísalo).

## Notas

- La primera vez que hables descarga el modelo de voz a texto (~500 MB, una sola vez).
- La voz del bot usa Edge TTS y necesita internet.
- Si el antivirus marca `uv.exe` de Hermes, es un falso positivo conocido (ver README de Hermes).
- Probado en Linux; en Windows las piezas específicas (atajos, reproducción, instalador) no han sido probadas todavía: si algo falla, abre un *issue* con el mensaje de error.

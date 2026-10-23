"""HomeBot: habla o escríbele a tu bot de Hermes con atajos de teclado.
  Windows + Y            empieza a grabar; otra vez Windows + Y para enviar
  Windows + Shift + Y    escribirle en una cajita
  Windows + Ctrl + Y     cortar la voz / cancelar
  python homebot.py --texto "hola"   prueba sin micrófono ni atajos
"""
import asyncio, os, re, subprocess, sys, tempfile, threading, time, wave
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DATOS = AQUI / "datos"; DATOS.mkdir(exist_ok=True)
PERFIL = os.environ.get("HOMEBOT_PERFIL", "homebot")
SESION = "homebot-sesion"
VOZ = os.environ.get("HOMEBOT_VOZ", "es-MX-DaliaNeural")
CREAR_SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def preguntar(texto: str) -> str:
    """Una consulta a Hermes (perfil propio, sesión que recuerda la charla)."""
    q = DATOS / "pregunta.txt"; q.write_text(texto, encoding="utf-8")
    r = subprocess.run(
        ["hermes", "-p", PERFIL, "chat", "-Q", "--oneshot", "--continue", SESION, "--create-if-missing",
         "--query-file", str(q)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=CREAR_SIN_VENTANA,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    lineas = [l for l in r.stdout.splitlines() if not re.match(r"^(session_id:|↻|Session )", l)]
    return "\n".join(lineas).strip()


_modelo = None
def transcribir(audio) -> str:
    global _modelo
    from faster_whisper import WhisperModel
    if _modelo is None:
        _modelo = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = _modelo.transcribe(audio, language="es", vad_filter=True, beam_size=1)
    return " ".join(s.text.strip() for s in segs).strip()


def sintetizar(texto: str, salida: Path) -> None:
    import edge_tts
    limpio = re.sub(r"[*_`#]", "", texto)
    asyncio.run(edge_tts.Communicate(limpio, VOZ).save(str(salida)))


def reproducir(mp3: Path) -> None:
    """Windows: MediaPlayer de PowerShell (no necesita instalar nada). Otros sistemas: ffplay si existe."""
    if os.name == "nt":
        ps = ("Add-Type -AssemblyName presentationCore; $p=New-Object System.Windows.Media.MediaPlayer; "
              f"$p.Open([uri]'{mp3}'); $p.Play(); Start-Sleep -Milliseconds 700; "
              "while(-not $p.NaturalDuration.HasTimeSpan){Start-Sleep -Milliseconds 100}; "
              "Start-Sleep -Milliseconds ([int]$p.NaturalDuration.TimeSpan.TotalMilliseconds + 300)")
        _voz.proc = subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                                     creationflags=CREAR_SIN_VENTANA)
    else:
        _voz.proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(mp3)])
    _voz.proc.wait()


class _voz:
    proc = None


def cortar_voz():
    if _voz.proc and _voz.proc.poll() is None:
        _voz.proc.terminate()


# ---------- ventana de estado/respuesta (tkinter, viene con Python) ----------
class Aviso:
    def __init__(self):
        import tkinter as tk
        self.tk = tk
        self.root = tk.Tk(); self.root.withdraw()
        self.win = None
        self.cola = []
        self.root.after(100, self._bombear)

    def mostrar(self, texto, segundos=0):
        self.cola.append(("mostrar", texto, segundos))

    def pedir_texto(self, cb):
        self.cola.append(("pedir", cb, 0))

    def _bombear(self):
        while self.cola:
            tipo, a, b = self.cola.pop(0)
            if tipo == "mostrar": self._mostrar(a, b)
            else: self._pedir(a)
        self.root.after(100, self._bombear)

    def _cerrar(self):
        if self.win: self.win.destroy(); self.win = None

    def _ventana(self):
        tk = self.tk; self._cerrar()
        w = tk.Toplevel(self.root); w.overrideredirect(True); w.attributes("-topmost", True)
        w.configure(bg="#1b1b24"); self.win = w
        return w

    def _colocar(self, w):
        w.update_idletasks()
        W, H = w.winfo_width(), w.winfo_height()
        w.geometry(f"+{w.winfo_screenwidth() - W - 24}+{w.winfo_screenheight() - H - 70}")

    def _mostrar(self, texto, segundos):
        tk = self.tk; w = self._ventana()
        tk.Label(w, text=texto, bg="#1b1b24", fg="#f2f2f7", font=("Segoe UI", 11), wraplength=420,
                 justify="left", padx=16, pady=12).pack()
        w.bind("<Button-1>", lambda e: self._cerrar())
        self._colocar(w)
        if segundos: w.after(int(segundos * 1000), lambda: self.win is w and self._cerrar())

    def _pedir(self, cb):
        tk = self.tk; w = self._ventana()
        e = tk.Entry(w, width=48, font=("Segoe UI", 12), bg="#2a2a36", fg="#f2f2f7", insertbackground="#f2f2f7", bd=0)
        e.pack(padx=14, pady=14, ipady=6)
        def enviar(_=None):
            t = e.get().strip(); self._cerrar()
            if t: threading.Thread(target=cb, args=(t,), daemon=True).start()
        e.bind("<Return>", enviar); e.bind("<Escape>", lambda _e: self._cerrar())
        self._colocar(w); w.focus_force(); e.focus_force()


def responder(texto: str, aviso: "Aviso | None", hablar=True) -> str:
    if aviso: aviso.mostrar("Pensando…")
    r = preguntar(texto)
    if not r:
        if aviso: aviso.mostrar("Sin respuesta. ¿Hay internet y la API key es correcta? (cambiar-clave.ps1)", 8)
        return ""
    if aviso: aviso.mostrar(r, 0)
    if hablar:
        try:
            mp3 = DATOS / "voz.mp3"; sintetizar(r, mp3); reproducir(mp3)
        except Exception as ex:
            if aviso: aviso.mostrar(r + f"\n\n(la voz falló: {ex})", 0)
    return r


class Grabadora:
    def __init__(self): self.stream = None; self.trozos = []
    def activa(self): return self.stream is not None
    def empezar(self):
        import sounddevice as sd
        self.trozos = []
        self.stream = sd.InputStream(samplerate=16000, channels=1, dtype="float32",
                                     callback=lambda d, *_: self.trozos.append(d.copy()))
        self.stream.start()
    def terminar(self):
        import numpy as np
        self.stream.stop(); self.stream.close(); self.stream = None
        return np.concatenate(self.trozos).flatten() if self.trozos else None


def principal():
    import keyboard
    aviso = Aviso(); grab = Grabadora()

    def voz():
        if not grab.activa():
            cortar_voz(); grab.empezar(); aviso.mostrar("🎙  Escuchando…  (Windows + Y para enviar)")
            return
        audio = grab.terminar(); aviso.mostrar("Transcribiendo…")
        def trabajo():
            t = transcribir(audio) if audio is not None and len(audio) > 8000 else ""
            if not t: aviso.mostrar("No te escuché.", 3); return
            aviso.mostrar(f"Tú: {t}"); responder(t, aviso)
        threading.Thread(target=trabajo, daemon=True).start()

    def texto():
        cortar_voz(); aviso.pedir_texto(lambda t: responder(t, aviso))

    def parar():
        cortar_voz()
        if grab.activa(): grab.terminar()
        aviso._cerrar()

    keyboard.add_hotkey("windows+y", voz, suppress=True)
    keyboard.add_hotkey("windows+shift+y", texto, suppress=True)
    keyboard.add_hotkey("windows+ctrl+y", parar, suppress=True)
    aviso.mostrar("HomeBot listo. Windows + Y para hablar.", 4)
    aviso.root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--texto":
        sin_voz = "--sin-voz" in sys.argv
        print(responder(" ".join(a for a in sys.argv[2:] if a != "--sin-voz"), None, hablar=not sin_voz))
    else:
        principal()

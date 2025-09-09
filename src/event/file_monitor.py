"""
Monitor de carpeta con Watchdog:
- Procesa archivos ya existentes al iniciar (barrido inicial)
- Detecta nuevos/movidos/modificados
- Llama un callback con Path del archivo
- Soporta shares UNC y movimientos entre volúmenes (shutil.move)
"""
import os
import time
import shutil
import logging
from pathlib import Path
from typing import Callable, List, Optional, Dict
from datetime import datetime

from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from src.core import settings

logger = logging.getLogger(__name__)


def _is_file_stable(file: Path, wait_ms: int = 800) -> bool:
    """Verifica que el archivo haya terminado de copiarse comparando tamaños."""
    try:
        s1 = file.stat().st_size
        time.sleep(max(0.05, wait_ms / 1000.0))
        s2 = file.stat().st_size
        return s1 == s2 and s2 > 0
    except FileNotFoundError:
        return False


class FileHandler(FileSystemEventHandler):
    """Manejador de eventos: on_created / on_moved / on_modified."""

    def __init__(self, callback: Callable[[Path], None], allowed_extensions: List[str], debounce_sec: float = 1.0):
        self.callback = callback
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
        self.debounce_sec = max(0.1, float(debounce_sec))
        self._recent: Dict[Path, float] = {}
        logger.info(f"📁 Manejador inicializado para extensiones: {self.allowed_extensions}")

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self._process(Path(event.src_path))

    def on_moved(self, event: FileSystemEvent):
        if not event.is_directory and getattr(event, "dest_path", None):
            self._process(Path(event.dest_path))

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            self._process(Path(event.src_path))

    def _process(self, file: Path):
        """Validaciones + callback si procede."""
        try:
            # Debounce por path
            now = time.time()
            last = self._recent.get(file)
            if last and (now - last) < self.debounce_sec:
                return
            self._recent[file] = now

            if not file.exists():
                return

            size = file.stat().st_size
            if size == 0:
                return

            if file.suffix.lower() not in self.allowed_extensions:
                return

            max_mb = settings.max_file_size_mb
            if (size / (1024 * 1024)) > max_mb:
                logger.warning(f"⚠️ Archivo muy grande: {file.name}")
                return

            # Esperar a que termine de copiarse
            if not _is_file_stable(file, wait_ms=max(800, settings.retry_delay_ms)):
                time.sleep(max(0.2, settings.retry_delay_ms / 1000.0))
                if not _is_file_stable(file, wait_ms=max(800, settings.retry_delay_ms)):
                    logger.debug(f"⏳ Aún inestable: {file.name}")
                    return

            logger.info(f"📥 Detectado: {file.name} ({size} bytes) ruta='{file}'")
            self.callback(file)

        except Exception as e:
            logger.error(f"❌ Error procesando archivo {file}: {e}", exc_info=True)


class FileMonitor:
    """Encapsula Observer / PollingObserver y el ciclo de vida del monitoreo."""

    def __init__(self):
        self.observer: Optional[Observer] = None # type: ignore
        self.is_monitoring: bool = False
        self.callback: Optional[Callable[[Path], None]] = None

        self.monitor_folder: Path = settings.shared_folder
        self.allowed_extensions: List[str] = settings.monitoring_allowed_extensions
        self.check_interval: int = max(1, int(settings.monitoring_interval_seconds))

        # Si quieres forzar polling (más compatible en shares/red), pon True desde main
        self.use_polling: bool = False

        logger.info("📋 Config monitoreo:")
        logger.info(f"   📁 Carpeta: {self.monitor_folder}")
        logger.info(f"   📝 Extensiones: {self.allowed_extensions}")
        logger.info(f"   ⏰ Intervalo: {self.check_interval}s")

    def _initial_sweep(self) -> None:
        """Procesa archivos ya existentes al iniciar (si son válidos/estables)."""
        try:
            count = 0
            for p in self.monitor_folder.glob("*"):
                if not p.is_file():
                    continue
                if p.suffix.lower() not in [e.lower() for e in self.allowed_extensions]:
                    continue
                if p.stat().st_size <= 0:
                    continue
                if not _is_file_stable(p, wait_ms=max(800, settings.retry_delay_ms)):
                    continue
                logger.info(f"🔎 Barrido inicial: {p.name}")
                self._handle_file(p)
                count += 1
            if count:
                logger.info(f"✅ Barrido inicial procesó {count} archivo(s).")
            else:
                logger.info("ℹ️ Barrido inicial: sin archivos candidatos.")
        except Exception as e:
            logger.warning(f"⚠️ Error en barrido inicial: {e}", exc_info=True)

    def start(self, callback: Callable[[Path], None]) -> bool:
        """Inicia el monitoreo en la carpeta configurada."""
        try:
            self.monitor_folder.mkdir(parents=True, exist_ok=True)
            self.callback = callback
            handler = FileHandler(self._handle_file, self.allowed_extensions, debounce_sec=1.0)
            watch_path = str(self.monitor_folder.resolve())

            try:
                if self.use_polling:
                    raise RuntimeError("Polling forzado por configuración")

                # Observer nativo
                self.observer = Observer()
                self.observer.schedule(handler, watch_path, recursive=False)
                self.observer.start()
                self.is_monitoring = True
                logger.info(f"🚀 Monitoreo iniciado (Observer nativo) en: {watch_path}")
            except Exception as native_err:
                # Fallback: polling (ideal para UNC/SMB)
                logger.warning(f"⚠️ Falló Observer nativo → PollingObserver: {native_err}")
                self.observer = PollingObserver(timeout=1.0)
                self.observer.schedule(handler, watch_path, recursive=False)
                self.observer.start()
                self.is_monitoring = True
                logger.info(f"🚀 Monitoreo iniciado (PollingObserver) en: {watch_path}")

            # Barrido inicial
            self._initial_sweep()
            return True
        except Exception as e:
            logger.error(f"❌ Error iniciando monitoreo: {e}", exc_info=True)
            return False

    def stop(self) -> None:
        """Detiene el monitoreo (seguro en errores/teardown)."""
        if self.observer and self.is_monitoring:
            try:
                self.observer.stop()
                self.observer.join(timeout=3.0)
            except Exception as e:
                logger.warning(f"⚠️ Error al detener observer: {e}", exc_info=True)
            finally:
                self.is_monitoring = False
                logger.info("⏹️ Monitoreo detenido")

    def _handle_file(self, file_path: Path) -> None:
        """Envuelve el callback del usuario con logs/seguridad."""
        try:
            if self.callback:
                logger.info(f"🎯 Callback: {file_path.name}")
                self.callback(file_path)
            else:
                logger.warning("⚠️ No hay callback configurado")
        except Exception as e:
            logger.error(f"❌ Error en callback para {file_path.name}: {e}", exc_info=True)

    def run_continuous(self, callback: Callable[[Path], None]) -> None:
        """Modo bloqueante sencillo (si no usas tu propio bucle principal)."""
        if not self.start(callback):
            return
        try:
            while self.is_monitoring:
                time.sleep(self.check_interval)
        finally:
            self.stop()


# ===== Utilidades extra =====

def get_file_info(file_path: Path) -> dict:
    """Información básica del archivo (útil para logs o UI)."""
    st = file_path.stat()
    return {
        "name": file_path.name,
        "size": st.st_size,
        "size_mb": st.st_size / (1024 * 1024),
        "created": datetime.fromtimestamp(st.st_ctime),
        "modified": datetime.fromtimestamp(st.st_mtime),
        "extension": file_path.suffix.lower(),
        "path": str(file_path),
    }


def move_file(source: Path, destination: Path) -> bool:
    """
    Mover archivo de forma segura (soporta cross-volume/UNC).
    Usa shutil.move: si es otro volumen, copia y luego elimina.
    """
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        logger.info(f"📦 Archivo movido: {source.name} → {destination}")
        return True
    except Exception as e:
        logger.error(f"❌ Error moviendo {source.name} → {destination}: {e}", exc_info=True)
        return False


def archive_file(file_path: Path) -> bool:
    """
    Mover a processed con sufijo timestamp (respetando settings.move_processed_files).
    Usa move_file (shutil.move) para soportar UNC/otra unidad.
    """
    if not settings.move_processed_files:
        return True
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = settings.processed_folder / f"{file_path.stem}_{ts}{file_path.suffix}"
        return move_file(file_path, dst)
    except Exception as e:
        logger.error(f"❌ Error archivando {file_path.name}: {e}", exc_info=True)
        return False

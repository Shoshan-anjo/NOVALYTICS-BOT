#!/usr/bin/env python3
"""
NOVALYTICS-BOT - Orquestador:
Login → ir a 'Iniciar Análisis' → monitor de carpeta → subir archivos detectados.
(Arreglo de hilos: el callback solo encola; el hilo principal procesa la cola)
"""

import logging
import time
from queue import Queue, Empty
from pathlib import Path
from src.core import settings
from src.robot.auth import demo_login
from src.robot.analisis import perform_upload
from src.event.file_monitor import FileMonitor, archive_file

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("🚀 Iniciando NOVALYTICS-BOT")
    settings.ensure_directories_exist()

    logger.info(f"📦 App: {settings.app_name} v{settings.app_version}")
    logger.info(f"🌍 Entorno: {settings.environment}")
    logger.info(f"🌐 Base URL: {settings.base_url}")
    logger.info(f"📁 Carpeta observada: {settings.shared_folder}")
    logger.info(f"🔗 Login URL: {settings.login_url} | 🔗 Análisis URL: {settings.analisis_url}")

    # 1) Login y abrir /iniciar-analisis (todo en hilo principal)
    pw, browser, context, page = demo_login()
    logger.info("✅ Sesión lista en 'Iniciar análisis'.")

    # 2) Cola para pasar trabajos del hilo del monitor → hilo principal
    work_q: Queue[Path] = Queue()

    def on_file_detected(p: Path):
        """Este callback corre en hilo del observer → SOLO ENCOLA."""
        logger.info(f"📥 Detectado → {p.name}")
        work_q.put(p)

    # 3) Iniciar monitor (hilo propio internamente)
    monitor = FileMonitor()
    if not monitor.start(on_file_detected):
        logger.error("❌ No se pudo iniciar el monitor. Revisa SHARED_FOLDER y permisos.")
        try:
            context.close(); browser.close(); pw.stop()
        except Exception:
            pass
        return

    logger.info("🚚 Automatización activa. Deja archivos en la carpeta para subirlos.")
    logger.info("🛑 Para salir usa Ctrl+C en la consola.")

    # 4) Bucle principal: consume cola y sube archivos SIEMPRE en este hilo
    try:
        while True:
            try:
                p: Path = work_q.get(timeout=1.0)  # espera 1 seg por nuevos archivos
            except Empty:
                # Nada nuevo; sigue procesando eventos del navegador
                time.sleep(0.2)
                continue

            try:
                logger.info(f"📤 Subiendo archivo: {p.name}")
                perform_upload(page, p)  # ← mismo hilo que creó 'page'
                logger.info(f"✅ Subido → {p.name}")

                if settings.move_processed_files:
                    archive_file(p)
                elif settings.delete_after_processing:
                    p.unlink(missing_ok=True)
                    logger.info(f"🗑️ Eliminado → {p.name}")

            except Exception as e:
                logger.exception(f"❌ Falló la subida de {p.name}: {e}")
            finally:
                work_q.task_done()

    except KeyboardInterrupt:
        logger.info("⏹️ Interrumpido por usuario.")
    finally:
        try: monitor.stop()
        except Exception: pass
        try: context.close()
        except Exception: pass
        try: browser.close()
        except Exception: pass
        try: pw.stop()
        except Exception: pass
        logger.info("✅ Recursos cerrados.")


if __name__ == "__main__":
    main()

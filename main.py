#!/usr/bin/env python3
"""
NOVALYTICS-BOT - Punto de entrada principal con:
- Login y navegación a 'Iniciar análisis'
- Monitor de carpeta (Watchdog, en cola)
- Keepalive periódico para evitar expiración de sesión
"""

import logging
import time
import threading
from queue import Queue, Empty
from pathlib import Path

from src.core import settings
from src.robot.auth import demo_login
from src.robot.analisis import perform_upload
from src.event.file_monitor import FileMonitor, archive_file

# ---- Logging global ----
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=getattr(logging, str(settings.log_level).upper(), logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# FUNCIONES PRINCIPALES
# ============================================================

def keep_session_alive(page):
    """
    Envía un 'ping' ligero para renovar cookies/sesión.
    Puede correrse en hilo paralelo.
    """
    while True:
        try:
            if not page:
                break
            # 1) Microactividad
            page.mouse.move(1, 1)
            page.mouse.move(2, 2)
            # 2) HEAD al backend
            page.evaluate(
                """(url) => { try { fetch(url, { method: 'HEAD', cache: 'no-store' }); } catch(e) {} }""",
                settings.home_url or settings.base_url
            )
            # 3) Marca local
            page.evaluate("""() => localStorage.setItem('nlb_keepalive', String(Date.now()))""")
            logger.debug("💓 keepalive enviado")
        except Exception as e:
            logger.warning(f"⚠️ keepalive falló: {e}")
        # Intervalo de mantenimiento
        time.sleep(max(60, getattr(settings, "keepalive_interval", 120)))


def process_file(fpath: Path):
    """
    Maneja el login, subida y post-proceso del archivo detectado.
    """
    pw = browser = context = page = None
    logger.info(f"📂 Iniciando flujo de análisis para {fpath.name}")

    try:
        pw, browser, context, page = demo_login()
        logger.info("✅ Sesión lista en 'Iniciar análisis'.")

        # Hilo keepalive (opcional)
        if getattr(settings, "enable_keepalive", False):
            threading.Thread(target=keep_session_alive, args=(page,), daemon=True).start()

        # Subir archivo y esperar resultado
        perform_upload(page, fpath)
        logger.info("📤 Archivo subido, esperando estado del análisis...")

        try:
            page.wait_for_selector("h5.mb-2", timeout=120000)
            logger.info("✅ Estado del análisis detectado: proceso completado.")
        except Exception as e:
            logger.warning(f"⚠️ No se detectó el estado del análisis: {e}")

        # Post-proceso (mover o eliminar)
        try:
            if settings.move_processed_files:
                archive_file(fpath)
            elif settings.delete_after_processing:
                fpath.unlink(missing_ok=True)
                logger.info(f"🗑️ Archivo eliminado: {fpath.name}")
        except Exception as e:
            logger.warning(f"⚠️ Falló post-proceso del archivo: {e}")

    except Exception as e:
        logger.error(f"❌ Falló el flujo con {fpath.name}: {e}", exc_info=True)

    finally:
        # Cierre seguro de Playwright
        for obj_name, obj in [("context", context), ("browser", browser), ("pw", pw)]:
            try:
                if obj:
                    obj.close() if hasattr(obj, "close") else obj.stop()
                    logger.debug(f"🧹 Cerrado {obj_name}")
            except Exception:
                pass

        logger.info("✅ Navegador cerrado tras procesar archivo.")


# ============================================================
# MAIN LOOP
# ============================================================

def main():
    logger.info("🚀 Iniciando NOVALYTICS-BOT")
    settings.ensure_directories_exist()

    logger.info(f"📦 App: {settings.app_name} v{settings.app_version}")
    logger.info(f"🌍 Entorno: {settings.environment}")
    logger.info(f"🌐 Base URL: {settings.base_url}")
    logger.info(f"📁 Carpeta observada: {settings.shared_folder}")
    logger.info(f"🔗 Login URL: {settings.login_url}")
    logger.info(f"🔗 Análisis URL: {settings.analisis_url}")

    q: Queue[Path] = Queue()

    # Callback del monitor
    def on_file_detected(p: Path):
        if p.suffix.lower() in settings.allowed_file_extensions:
            logger.info(f"📥 Archivo Excel detectado: {p.name}")
            q.put(p)
        else:
            logger.info(f"📄 Archivo ignorado (extensión no válida): {p.name}")

    # Iniciar monitor
    mon = FileMonitor()
    mon.use_polling = getattr(settings, "force_polling", False)
    started = mon.start(on_file_detected)

    if not started:
        logger.error("❌ No se pudo iniciar el monitor de carpeta.")
        return

    logger.info("🚚 Automatización activa. Deja archivos Excel en la carpeta para subirlos.")
    logger.info("⏸️ Presiona CTRL+C para terminar.")

    try:
        while True:
            try:
                fpath = q.get(timeout=1.0)
            except Empty:
                continue
            process_file(fpath)

    except KeyboardInterrupt:
        logger.info("⏹️ Interrupción manual detectada. Cerrando...")

    finally:
        mon.stop()
        logger.info("✅ NOVALYTICS-BOT finalizado correctamente.")


if __name__ == "__main__":
    main()

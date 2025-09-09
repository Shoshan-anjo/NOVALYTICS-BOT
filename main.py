#!/usr/bin/env python3
"""
NOVALYTICS-BOT - Punto de entrada principal con:
- Login y navegación a 'Iniciar análisis'
- Monitor de carpeta (Watchdog, en cola)
- Keepalive periódico para evitar expiración de sesión
"""

import logging
import time
from queue import Queue, Empty
from pathlib import Path

from src.core import settings
from src.robot.auth import demo_login
from src.robot.analisis import perform_upload
from src.event.file_monitor import FileMonitor, archive_file

# ---- Logging ----
logging.basicConfig(
    level=getattr(logging, str(settings.log_level).upper(), logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def keep_session_alive(page):
    """
    Envía un 'ping' ligero para que el backend renueve cookies/sesión
    sin interrumpir la vista actual. Debe correr en el mismo hilo que 'page'.
    """
    try:
        # 1) Micro actividad
        page.mouse.move(1, 1)
        page.mouse.move(2, 2)
        # 2) HEAD ligera (si el backend lo permite)
        page.evaluate(
            """(url) => { try { fetch(url, { method: 'HEAD', cache: 'no-store' }); } catch(e) {} }""",
            settings.home_url or settings.base_url
        )
        # 3) Marca local
        page.evaluate("""() => localStorage.setItem('nlb_keepalive', String(Date.now()))""")
        logger.debug("💓 keepalive enviado")
    except Exception as e:
        logger.warning(f"⚠️ keepalive falló: {e}")


def main():
    logger.info("🚀 Iniciando NOVALYTICS-BOT")
    # Asegurar carpetas
    settings.ensure_directories_exist()

    # Info de entorno
    logger.info(f"📦 App: {settings.app_name} v{settings.app_version}")
    logger.info(f"🌍 Entorno: {settings.environment}")
    logger.info(f"🌐 Base URL: {settings.base_url}")
    logger.info(f"📁 Carpeta observada: {settings.shared_folder}")
    logger.info(f"🔗 Login URL: {settings.login_url} | 🔗 Análisis URL: {settings.analisis_url}")

    # Login + quedar en Iniciar Análisis
    pw, browser, context, page = demo_login()
    logger.info("✅ Sesión lista en 'Iniciar análisis'.")

    # ---- Monitor + Cola (mismo hilo que 'page') ----
    q: Queue[Path] = Queue()

    def on_file_detected(p: Path):
        # Esta función corre en otro hilo (watchdog), así que solo encolamos
        q.put(p)

    mon = FileMonitor()
    mon.use_polling = True  # fuerza PollingObserver para máxima compatibilidad en Windows
    mon.start(on_file_detected)

    logger.info("🚚 Automatización activa. Deja archivos en la carpeta para subirlos.")
    logger.info("⏸️ Presiona CTRL+C para terminar.")

    last_keepalive = 0.0
    KEEPALIVE_EVERY_SEC = 60  # ajusta si el backend expira antes (p.ej. 45)

    try:
        while True:
            # Keepalive
            now = time.time()
            if now - last_keepalive > KEEPALIVE_EVERY_SEC:
                keep_session_alive(page)
                last_keepalive = now

            # Procesar cola de archivos (en el MISMO hilo de page)
            try:
                fpath = q.get(timeout=1.0)
            except Empty:
                continue

            try:
                logger.info(f"📥 Detectado → {fpath.name}")
                perform_upload(page, fpath)

                # Mover/archivar según config
                try:
                    if settings.move_processed_files:
                        archive_file(fpath)
                    elif settings.delete_after_processing:
                        fpath.unlink(missing_ok=True)
                        logger.info(f"🗑️ Archivo eliminado: {fpath.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Post-proceso del archivo falló: {e}")

            except Exception as e:
                logger.error(f"❌ Falló el flujo de análisis con {fpath.name}: {e}", exc_info=True)

    except KeyboardInterrupt:
        logger.info("⏹️ Interrupción recibida. Cerrando...")

    finally:
        try:
            mon.stop()
        except Exception:
            pass
        # No cierres el navegador si quieres dejar la sesión viva tras parar el monitor.
        try:
            context.close()
        except Exception:
            pass
        try:
            browser.close()
        except Exception:
            pass
        try:
            pw.stop()
        except Exception:
            pass
        logger.info("✅ Finalizado.")


if __name__ == "__main__":
    main()

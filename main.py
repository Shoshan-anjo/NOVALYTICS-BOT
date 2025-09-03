#!/usr/bin/env python3
"""
NOVALYTICS-BOT - Punto de entrada principal usando Settings
"""

import logging
from src.core import settings
from src.robot.auth import demo_login

# Configurar logging con el nivel desde settings (int)
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Función principal usando Settings"""
    logger.info("🚀 Iniciando NOVALYTICS-BOT")

    # Asegurar que las carpetas existen
    settings.ensure_directories_exist()

    # Mostrar información de configuración
    logger.info(f"📦 Aplicación: {settings.app_name} v{settings.app_version}")
    logger.info(f"🌍 Entorno: {settings.environment}")
    logger.info(f"🌐 URL Base: {settings.base_url}")
    logger.info(f"📁 Carpeta compartida: {settings.shared_folder}")

    # Configuración del browser
    browser_config = settings.get_browser_config()
    logger.info(f"🖥️ Config browser: {browser_config}")

    # Configuración de análisis
    analisis_config = settings.get_analisis_config()
    logger.info(f"📊 Config análisis: {analisis_config['default_parametro']}")

    # Log de URLs clave para verificar placeholders resueltos
    logger.info(f"🔗 Login URL usada: {settings.login_url}")
    logger.info(f"🔗 Post-Login URL usada: {settings.post_login_url}")

    # Verificar credenciales
    if not settings.username or not settings.password:
        logger.warning("⚠️ Credenciales no configuradas (.env o config.json)")

    # 🔐 Probar login y tomar screenshot del dashboard
    demo_login()

    logger.info("✅ Flujo completado correctamente")

if __name__ == "__main__":
    main()

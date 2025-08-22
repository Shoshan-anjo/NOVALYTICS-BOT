#!/usr/bin/env python3
"""
NOVALYTICS-BOT - Punto de entrada principal usando Settings
"""

import asyncio
import logging
from src.core import settings

# Configurar logging con el nivel desde settings
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
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
    
    # Verificar credenciales
    if not settings.username or not settings.password:
        logger.warning("⚠️ Credenciales no configuradas en .env")
    
    # Aquí iría tu lógica principal de automatización...
    logger.info("✅ Configuración cargada correctamente")

if __name__ == "__main__":
    asyncio.run(main())
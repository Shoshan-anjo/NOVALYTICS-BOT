"""
Módulo principal de configuración para NOVALYTICS-BOT
Proporciona acceso fácil a toda la configuración de la aplicación
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config_loader import config

# Configurar logging
logger = logging.getLogger(__name__)

class Settings:
    """
    Clase de configuración principal que proporciona acceso fácil a todos los settings
    """
    
    # Singleton instance
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializar la configuración"""
        self._config = config.get_all()
        logger.info("✅ Settings inicializado")
    
    @property
    def app_name(self) -> str:
        """Nombre de la aplicación"""
        return config.get('app.name', 'NOVALYTICS-BOT')
    
    @property
    def app_version(self) -> str:
        """Versión de la aplicación"""
        return config.get('app.version', '1.0.0')
    
    @property
    def environment(self) -> str:
        """Entorno de ejecución"""
        return config.get('app.environment', 'development')
    
    @property
    def log_level(self) -> str:
        """Nivel de logging"""
        return config.get('app.log_level', 'INFO')
    
    # URLs
    @property
    def base_url(self) -> str:
        """URL base de la aplicación"""
        return config.get('urls.base_url')
    
    @property
    def home_url(self) -> str:
        """URL de la página principal"""
        return config.get('urls.home_url', self.base_url)
    
    @property
    def login_url(self) -> str:
        """URL de login"""
        return config.get('urls.login_url', f"{self.base_url}/login")
    
    @property
    def analisis_url(self) -> str:
        """URL de análisis"""
        return config.get('urls.analisis_url', f"{self.base_url}/iniciar-analisis")
    
    @property
    def configuracion_url(self) -> str:
        """URL de configuración"""
        return config.get('urls.configuracion_url', f"{self.base_url}/configuracion")
    
    @property
    def timeout(self) -> int:
        """Timeout general en milisegundos"""
        return config.get('urls.timeout', 30000)
    
    # Paths
    @property
    def shared_folder(self) -> Path:
        """Carpeta compartida para monitoreo"""
        folder_path = config.get('paths.shared_folder')
        return Path(folder_path) if folder_path else Path.cwd() / 'data' / 'shared'
    
    @property
    def downloads_folder(self) -> Path:
        """Carpeta de descargas"""
        folder_path = config.get('paths.downloads_folder', './data/downloads')
        return Path(folder_path)
    
    @property
    def uploads_folder(self) -> Path:
        """Carpeta de uploads"""
        folder_path = config.get('paths.uploads_folder', './data/uploads')
        return Path(folder_path)
    
    @property
    def screenshots_folder(self) -> Path:
        """Carpeta de screenshots"""
        folder_path = config.get('paths.screenshots_folder', './data/screenshots')
        return Path(folder_path)
    
    @property
    def logs_folder(self) -> Path:
        """Carpeta de logs"""
        folder_path = config.get('paths.logs_folder', './logs')
        return Path(folder_path)
    
    # Análisis
    @property
    def default_parametro(self) -> str:
        """Parámetro por defecto para análisis"""
        return config.get('analisis.default_parametro', '1')
    
    @property
    def default_servicio(self) -> str:
        """Servicio por defecto para análisis"""
        return config.get('analisis.default_servicio', '1')
    
    @property
    def allowed_file_extensions(self) -> List[str]:
        """Extensiones de archivo permitidas"""
        return config.get('analisis.allowed_file_extensions', ['.xlsx', '.xls'])
    
    @property
    def max_file_size_mb(self) -> int:
        """Tamaño máximo de archivo en MB"""
        return config.get('analisis.max_file_size_mb', 50)
    
    @property
    def wait_after_upload_ms(self) -> int:
        """Tiempo de espera después de upload en ms"""
        return config.get('analisis.wait_after_upload_ms', 2000)
    
    @property
    def wait_after_submit_ms(self) -> int:
        """Tiempo de espera después de submit en ms"""
        return config.get('analisis.wait_after_submit_ms', 10000)
    
    # Browser
    @property
    def browser_headless(self) -> bool:
        """Modo headless del navegador"""
        return config.get('browser.headless', False)
    
    @property
    def browser_slow_mo(self) -> int:
        """Slow motion para debugging"""
        return config.get('browser.slow_mo', 100)
    
    @property
    def browser_viewport_width(self) -> int:
        """Ancho del viewport"""
        return config.get('browser.viewport_width', 1280)
    
    @property
    def browser_viewport_height(self) -> int:
        """Alto del viewport"""
        return config.get('browser.viewport_height', 720)
    
    @property
    def browser_timeout(self) -> int:
        """Timeout del navegador en ms"""
        return config.get('browser.timeout', 30000)
    
    @property
    def browser_user_agent(self) -> str:
        """User agent del navegador"""
        return config.get('browser.user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Credenciales
    @property
    def username(self) -> Optional[str]:
        """Usuario de la aplicación"""
        return config.get('credentials.username')
    
    @property
    def password(self) -> Optional[str]:
        """Password de la aplicación"""
        return config.get('credentials.password')
    
    # Monitoring
    @property
    def monitoring_interval_seconds(self) -> int:
        """Intervalo de monitoreo en segundos"""
        return config.get('monitoring.check_interval_seconds', 60)
    
    @property
    def monitoring_allowed_extensions(self) -> List[str]:
        """Extensiones permitidas para monitoreo"""
        return config.get('monitoring.allowed_extensions', ['.xlsx', '.xls', '.csv'])
    
    @property
    def delete_after_processing(self) -> bool:
        """Eliminar archivos después de procesar"""
        return config.get('monitoring.delete_after_processing', False)
    
    @property
    def move_processed_files(self) -> bool:
        """Mover archivos después de procesar"""
        return config.get('monitoring.move_processed_files', True)
    
    @property
    def processed_folder(self) -> Path:
        """Carpeta para archivos procesados"""
        folder_path = config.get('monitoring.processed_folder', './data/processed')
        return Path(folder_path)
    
    # Retry
    @property
    def max_retry_attempts(self) -> int:
        """Máximo número de intentos de reintento"""
        return config.get('retry.max_attempts', 3)
    
    @property
    def retry_delay_ms(self) -> int:
        """Delay entre intentos en ms"""
        return config.get('retry.delay_between_attempts_ms', 2000)
    
    @property
    def retry_timeout_ms(self) -> int:
        """Timeout por intento en ms"""
        return config.get('retry.timeout_per_attempt_ms', 15000)
    
    # Métodos de utilidad
    def ensure_directories_exist(self):
        """Asegurar que todas las carpetas necesarias existan"""
        directories = [
            self.shared_folder,
            self.downloads_folder,
            self.uploads_folder,
            self.screenshots_folder,
            self.logs_folder,
            self.processed_folder
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Carpeta asegurada: {directory}")
    
    def is_production(self) -> bool:
        """Verificar si está en entorno de producción"""
        return self.environment.lower() == 'production'
    
    def is_development(self) -> bool:
        """Verificar si está en entorno de desarrollo"""
        return self.environment.lower() == 'development'
    
    def get_browser_config(self) -> Dict[str, Any]:
        """Obtener configuración completa del browser"""
        return {
            'headless': self.browser_headless,
            'slow_mo': self.browser_slow_mo,
            'viewport': {
                'width': self.browser_viewport_width,
                'height': self.browser_viewport_height
            },
            'timeout': self.browser_timeout
        }
    
    def get_analisis_config(self) -> Dict[str, Any]:
        """Obtener configuración completa de análisis"""
        return {
            'default_parametro': self.default_parametro,
            'default_servicio': self.default_servicio,
            'allowed_extensions': self.allowed_file_extensions,
            'max_file_size': self.max_file_size_mb,
            'wait_times': {
                'after_upload': self.wait_after_upload_ms,
                'after_submit': self.wait_after_submit_ms
            }
        }
    
    def reload(self):
        """Recargar configuración"""
        config.reload()
        self._initialize()
        logger.info("🔄 Configuración recargada")

# Instancia global singleton
settings = Settings()
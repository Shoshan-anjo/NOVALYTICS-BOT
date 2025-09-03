"""
Módulo principal de configuración para NOVALYTICS-BOT
Proporciona acceso fácil a toda la configuración de la aplicación
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config_loader import config

logger = logging.getLogger(__name__)

def _to_bool(value, default=False) -> bool:
    """Convierte str/bool/int a bool de forma robusta."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    return s in ("1", "true", "yes", "y", "on")

def has_placeholder(s):
    """Detecta placeholders sin resolver tipo {{VAR}}."""
    return isinstance(s, str) and ("{{" in s or "}}" in s)

def _join_url(base: str, path: str) -> str:
    """Une base y path sin duplicar /."""
    if not base:
        return path
    if base.endswith("/") and path.startswith("/"):
        return base[:-1] + path
    if (not base.endswith("/")) and (not path.startswith("/")):
        return base + "/" + path
    return base + path

class Settings:
    """Clase de configuración principal (singleton)."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Inicializar la configuración desde el config_loader."""
        self._config = config.get_all()
        logger.info("✅ Settings inicializado")

    # -------------------- App --------------------
    @property
    def app_name(self) -> str:
        return config.get('app.name', 'NOVALYTICS-BOT')

    @property
    def app_version(self) -> str:
        return config.get('app.version', '1.0.0')

    @property
    def environment(self) -> str:
        return config.get('app.environment', 'development')

    @property
    def log_level(self) -> int:
        """Devuelve el nivel de logging como entero."""
        level_str = str(config.get('app.log_level', 'INFO')).upper()
        return getattr(logging, level_str, logging.INFO)

    # -------------------- URLs --------------------
    @property
    def base_url(self) -> str:
        val = config.get('urls.base_url')
        env_val = os.getenv("BASE_URL")
        return env_val if has_placeholder(val) else (val or env_val or "")

    @property
    def home_url(self) -> str:
        val = config.get('urls.home_url')
        if has_placeholder(val) or not val:
            return self.base_url
        return val

    @property
    def login_url(self) -> str:
        # Prioriza .env
        env_login = os.getenv("LOGIN_URL")
        if env_login:
            return env_login
        # Si config quedó con {{...}} o vacío, construye desde base_url
        val = config.get('urls.login_url')
        if has_placeholder(val) or not val:
            return _join_url(self.base_url, "/login")
        return val

    @property
    def post_login_url(self) -> Optional[str]:
        env_post = os.getenv("POST_LOGIN_URL")
        if env_post:
            return env_post
        val = config.get('urls.post_login_url')
        if val is None or has_placeholder(val):
            return None
        return val

    @property
    def analisis_url(self) -> str:
        val = config.get('urls.analisis_url')
        if has_placeholder(val) or not val:
            return _join_url(self.base_url, "/iniciar-analisis")
        return val

    @property
    def configuracion_url(self) -> str:
        val = config.get('urls.configuracion_url')
        if has_placeholder(val) or not val:
            return _join_url(self.base_url, "/configuracion")
        return val

    @property
    def timeout(self) -> int:
        return int(config.get('urls.timeout', 30000))

    @property
    def navigation_timeout(self) -> int:
        return int(config.get('urls.navigation_timeout', 60000))

    # -------------------- Paths --------------------
    @property
    def shared_folder(self) -> Path:
        folder_path = config.get('paths.shared_folder') or os.getenv("SHARED_FOLDER")
        return Path(folder_path) if folder_path else Path.cwd() / 'data' / 'shared'

    @property
    def downloads_folder(self) -> Path:
        return Path(config.get('paths.downloads_folder', './data/downloads'))

    @property
    def uploads_folder(self) -> Path:
        return Path(config.get('paths.uploads_folder', './data/uploads'))

    @property
    def screenshots_folder(self) -> Path:
        return Path(config.get('paths.screenshots_folder', './data/screenshots'))

    @property
    def logs_folder(self) -> Path:
        return Path(config.get('paths.logs_folder', './logs'))

    @property
    def reports_folder(self) -> Path:
        return Path(config.get('paths.reports_folder', './data/reports'))

    @property
    def backups_folder(self) -> Path:
        return Path(config.get('paths.backup_folder', './data/backups'))

    @property
    def processed_folder(self) -> Path:
        return Path(config.get('monitoring.processed_folder', './data/processed'))

    # -------------------- Análisis --------------------
    @property
    def default_parametro(self) -> str:
        return config.get('analisis.default_parametro', '1')

    @property
    def default_servicio(self) -> str:
        return config.get('analisis.default_servicio', '1')

    @property
    def allowed_file_extensions(self) -> List[str]:
        return config.get('analisis.allowed_file_extensions', ['.xlsx', '.xls'])

    @property
    def max_file_size_mb(self) -> int:
        return int(config.get('analisis.max_file_size_mb', 50))

    @property
    def wait_after_upload_ms(self) -> int:
        return int(config.get('analisis.wait_after_upload_ms', 2000))

    @property
    def wait_after_submit_ms(self) -> int:
        return int(config.get('analisis.wait_after_submit_ms', 10000))

    # -------------------- Browser --------------------
    @property
    def browser_headless(self) -> bool:
        raw = config.get('browser.headless', os.getenv("PLAYWRIGHT_HEADLESS", "true"))
        return _to_bool(raw, default=True)

    @property
    def browser_slow_mo(self) -> int:
        return int(config.get('browser.slow_mo', 100))

    @property
    def browser_viewport_width(self) -> int:
        return int(config.get('browser.viewport_width', 1280))

    @property
    def browser_viewport_height(self) -> int:
        return int(config.get('browser.viewport_height', 720))

    @property
    def browser_timeout(self) -> int:
        return int(config.get('browser.timeout', 30000))

    @property
    def browser_user_agent(self) -> str:
        return config.get('browser.user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    # -------------------- Credenciales --------------------
    @property
    def username(self) -> Optional[str]:
        return config.get('credentials.username') or os.getenv("LOGIN_USERNAME")

    @property
    def password(self) -> Optional[str]:
        return config.get('credentials.password') or os.getenv("LOGIN_PASSWORD")

    # -------------------- Monitoring --------------------
    @property
    def monitoring_interval_seconds(self) -> int:
        return int(config.get('monitoring.check_interval_seconds', 60))

    @property
    def monitoring_allowed_extensions(self) -> List[str]:
        return config.get('monitoring.allowed_extensions', ['.xlsx', '.xls', '.csv'])

    @property
    def delete_after_processing(self) -> bool:
        return _to_bool(config.get('monitoring.delete_after_processing', False))

    @property
    def move_processed_files(self) -> bool:
        return _to_bool(config.get('monitoring.move_processed_files', True))

    # -------------------- Retry --------------------
    @property
    def max_retry_attempts(self) -> int:
        return int(config.get('retry.max_attempts', 3))

    @property
    def retry_delay_ms(self) -> int:
        return int(config.get('retry.delay_between_attempts_ms', 2000))

    @property
    def retry_timeout_ms(self) -> int:
        return int(config.get('retry.timeout_per_attempt_ms', 15000))

    # -------------------- Login/Storage extra --------------------
    @property
    def storage_state_path(self) -> Path:
        """Ruta del storage_state.json para sesión persistente."""
        return Path(os.getenv("STORAGE_STATE_PATH", "./data/auth/storage.json"))

    @property
    def login_timeout_ms(self) -> int:
        """Timeout para confirmar login OK."""
        return int(os.getenv("LOGIN_TIMEOUT_MS", config.get('urls.timeout', 30000)))

    @property
    def force_relogin(self) -> bool:
        """Forzar re-login ignorando storage_state previo."""
        return _to_bool(os.getenv("FORCE_RELOGIN", "false"))

    # -------------------- Utilidades --------------------
    def ensure_directories_exist(self):
        """Asegura que carpetas necesarias existan."""
        directories = [
            self.shared_folder,
            self.downloads_folder,
            self.uploads_folder,
            self.screenshots_folder,
            self.logs_folder,
            self.processed_folder,
            self.reports_folder,
            self.backups_folder,
            self.storage_state_path.parent,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Carpeta asegurada: {directory}")

    def is_production(self) -> bool:
        return self.environment.lower() == 'production'

    def is_development(self) -> bool:
        return self.environment.lower() == 'development'

    def get_browser_config(self) -> Dict[str, Any]:
        return {
            'headless': self.browser_headless,
            'slow_mo': self.browser_slow_mo,
            'viewport': {'width': self.browser_viewport_width, 'height': self.browser_viewport_height},
            'timeout': self.browser_timeout,
            'user_agent': self.browser_user_agent,
        }

    def get_analisis_config(self) -> Dict[str, Any]:
        return {
            'default_parametro': self.default_parametro,
            'default_servicio': self.default_servicio,
            'allowed_extensions': self.allowed_file_extensions,
            'max_file_size': self.max_file_size_mb,
            'wait_times': {'after_upload': self.wait_after_upload_ms, 'after_submit': self.wait_after_submit_ms},
        }

    def reload(self):
        config.reload()
        self._initialize()
        logger.info("🔄 Configuración recargada")

# Instancia global singleton
settings = Settings()

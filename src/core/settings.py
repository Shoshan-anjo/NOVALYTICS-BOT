# src/core/settings.py
"""
Settings central para NOVALYTICS-BOT.
Lee valores desde config_loader (que ya resuelve .env + config.json).
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config_loader import config

logger = logging.getLogger(__name__)


def has_placeholder(value: str) -> bool:
    """True si el string contiene {{PLACEHOLDER}}."""
    return isinstance(value, str) and "{{" in value and "}}" in value


class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._config = config.get_all()
        logger.info("✅ Settings inicializado")

    # ========= App =========
    @property
    def app_name(self) -> str:
        return config.get("app.name", "NOVALYTICS-BOT")

    @property
    def app_version(self) -> str:
        return config.get("app.version", "1.0.0")

    @property
    def environment(self) -> str:
        return config.get("app.environment", "development")

    @property
    def log_level(self) -> int:
        """
        Nivel de logging como INT (INFO/DEBUG/ERROR).
        Convierte desde texto del config.json (app.log_level).
        """
        level_str = str(config.get("app.log_level", "INFO")).upper()
        return getattr(logging, level_str, logging.INFO)
    # ========= URLs =========
    @property
    def base_url(self) -> str:
        raw = config.get("urls.base_url")
        if not isinstance(raw, str) or has_placeholder(raw):
            raise ValueError("urls.base_url no resuelto. Revisa BASE_URL en .env o config.json.")
        # normaliza: sin slash final
        return raw.rstrip("/")

    def _ensure_url(self, value: str | None, fallback_path: str) -> str:
        """
        Si value es None o tiene {{PLACEHOLDER}}, construye self.base_url + fallback_path.
        Garantiza que la URL final sea absoluta.
        """
        if not isinstance(value, str) or has_placeholder(value) or not value.startswith(("http://", "https://")):
            return f"{self.base_url}/{fallback_path.lstrip('/')}"
        return value

    @property
    def home_url(self) -> str:
        raw = config.get("urls.home_url")
        return self._ensure_url(raw, "")

    @property
    def login_url(self) -> str:
        raw = config.get("urls.login_url")
        return self._ensure_url(raw, "/login")

    @property
    def analisis_url(self) -> str:
        raw = config.get("urls.analisis_url")
        return self._ensure_url(raw, "/iniciar-analisis")

    @property
    def configuracion_url(self) -> str:
        raw = config.get("urls.configuracion_url")
        return self._ensure_url(raw, "/configuracion")

    @property
    def timeout(self) -> int:
        return int(config.get("urls.timeout", 30000))

    @property
    def navigation_timeout(self) -> int:
        return int(config.get("urls.navigation_timeout", 60000))

    # ========= Paths =========
    @property
    def shared_folder(self) -> Path:
        folder_path = config.get("paths.shared_folder")
        return Path(folder_path) if folder_path else Path.cwd() / "data" / "shared"

    @property
    def downloads_folder(self) -> Path:
        return Path(config.get("paths.downloads_folder", "./data/downloads"))

    @property
    def uploads_folder(self) -> Path:
        return Path(config.get("paths.uploads_folder", "./data/uploads"))

    @property
    def screenshots_folder(self) -> Path:
        return Path(config.get("paths.screenshots_folder", "./data/screenshots"))

    @property
    def logs_folder(self) -> Path:
        return Path(config.get("paths.logs_folder", "./logs"))

    @property
    def reports_folder(self) -> Path:
        return Path(config.get("paths.reports_folder", "./data/reports"))

    @property
    def backups_folder(self) -> Path:
        return Path(config.get("paths.backup_folder", "./data/backups"))

    # ========= Análisis =========
    @property
    def default_parametro(self) -> str:
        return str(config.get("analisis.default_parametro", "1"))

    @property
    def default_servicio(self) -> str:
        return str(config.get("analisis.default_servicio", "1"))

    @property
    def allowed_file_extensions(self) -> List[str]:
        return list(config.get("analisis.allowed_file_extensions", [".xlsx", ".xls"]))

    @property
    def max_file_size_mb(self) -> int:
        return int(config.get("analisis.max_file_size_mb", 50))

    @property
    def wait_after_upload_ms(self) -> int:
        return int(config.get("analisis.wait_after_upload_ms", 2000))

    @property
    def wait_after_submit_ms(self) -> int:
        return int(config.get("analisis.wait_after_submit_ms", 10000))

    # ========= Browser =========
    @property
    def browser_headless(self) -> bool:
        v = config.get("browser.headless", False)
        if isinstance(v, str):
            return v.strip().lower() == "true"
        return bool(v)

    @property
    def browser_slow_mo(self) -> int:
        return int(config.get("browser.slow_mo", 100))

    @property
    def browser_viewport_width(self) -> int:
        return int(config.get("browser.viewport_width", 1280))

    @property
    def browser_viewport_height(self) -> int:
        return int(config.get("browser.viewport_height", 720))

    @property
    def browser_timeout(self) -> int:
        return int(config.get("browser.timeout", 30000))

    @property
    def browser_user_agent(self) -> str:
        return config.get(
            "browser.user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )

    # ========= Credenciales =========
    @property
    def username(self) -> Optional[str]:
        return config.get("credentials.username") or config.get("APP_USERNAME")

    @property
    def password(self) -> Optional[str]:
        return config.get("credentials.password") or config.get("APP_PASSWORD")

    # ========= Monitoring =========
    @property
    def monitoring_interval_seconds(self) -> int:
        return int(config.get("monitoring.check_interval_seconds", 60))

    @property
    def monitoring_allowed_extensions(self) -> List[str]:
        return list(config.get("monitoring.allowed_extensions", [".xlsx", ".xls", ".csv"]))

    @property
    def delete_after_processing(self) -> bool:
        v = config.get("monitoring.delete_after_processing", False)
        if isinstance(v, str):
            return v.strip().lower() == "true"
        return bool(v)

    @property
    def move_processed_files(self) -> bool:
        v = config.get("monitoring.move_processed_files", True)
        if isinstance(v, str):
            return v.strip().lower() == "true"
        return bool(v)

    @property
    def processed_folder(self) -> Path:
        return Path(config.get("monitoring.processed_folder", "./data/processed"))

    # ========= Retry =========
    @property
    def max_retry_attempts(self) -> int:
        return int(config.get("retry.max_attempts", 3))

    @property
    def retry_delay_ms(self) -> int:
        return int(config.get("retry.delay_between_attempts_ms", 2000))

    @property
    def retry_timeout_ms(self) -> int:
        return int(config.get("retry.timeout_per_attempt_ms", 15000))

    # ========= Login/Playwright extra =========
    @property
    def storage_state_path(self) -> Path:
        return Path(config.get("STORAGE_STATE_PATH", "./data/auth/storage.json"))

    @property
    def login_timeout_ms(self) -> int:
        return int(config.get("LOGIN_TIMEOUT_MS", 30000))

    @property
    def force_relogin(self) -> bool:
        v = config.get("FORCE_RELOGIN", "false")
        return str(v).strip().lower() == "true"

    @property
    def post_login_url(self) -> Optional[str]:
        v = config.get("POST_LOGIN_URL", None)
        return v if v else None

    # ========= Helpers =========
    def ensure_directories_exist(self):
        """Crea todas las carpetas necesarias si no existen."""
        directories = [
            self.shared_folder,
            self.downloads_folder,
            self.uploads_folder,
            self.screenshots_folder,
            self.logs_folder,
            self.processed_folder,
            self.reports_folder,
            self.backups_folder,
            Path("./data/auth"),
        ]
        for d in directories:
            d.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Carpeta asegurada: {d}")

    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    def get_browser_config(self) -> Dict[str, Any]:
        return {
            "headless": self.browser_headless,
            "slow_mo": self.browser_slow_mo,
            "viewport": {"width": self.browser_viewport_width, "height": self.browser_viewport_height},
            "timeout": self.browser_timeout,
            "user_agent": self.browser_user_agent,
        }

    def get_analisis_config(self) -> Dict[str, Any]:
        return {
            "default_parametro": self.default_parametro,
            "default_servicio": self.default_servicio,
            "allowed_extensions": self.allowed_file_extensions,
            "max_file_size": self.max_file_size_mb,
            "wait_times": {
                "after_upload": self.wait_after_upload_ms,
                "after_submit": self.wait_after_submit_ms,
            },
        }

    def reload(self):
        config.reload()
        self._initialize()
        logger.info("🔄 Configuración recargada")


# instancia singleton
settings = Settings()

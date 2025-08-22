"""
Cargador inteligente de configuración para NOVALYTICS-BOT
Combina variables de entorno (.env) con configuración JSON (config.json)
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Cargador de configuración que unifica .env y config.json
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config: Dict[str, Any] = {}
        self._load_environment()
        self._load_config_file()
        self._validate_config()
        
        self._initialized = True
        logger.info("✅ ConfigLoader inicializado correctamente")
    
    def _load_environment(self):
        """Cargar variables de entorno desde .env"""
        try:
            # Buscar .env en el directorio raíz del proyecto
            env_path = Path(__file__).parent.parent.parent / '.env'
            
            if env_path.exists():
                load_dotenv(dotenv_path=env_path)
                logger.info("✅ Variables de entorno cargadas desde .env")
            else:
                logger.warning("⚠️  Archivo .env no encontrado. Usando variables de sistema.")
                
        except Exception as e:
            logger.error(f"❌ Error cargando variables de entorno: {e}")
    
    def _load_config_file(self):
        """Cargar y procesar archivo config.json"""
        try:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'config.json'
            
            if not config_path.exists():
                raise FileNotFoundError(f"Archivo config.json no encontrado en: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                raw_config = json.load(f)
            
            # Procesar y reemplazar variables de entorno
            self.config = self._process_config(raw_config)
            logger.info("✅ Configuración cargada desde config.json")
            
        except FileNotFoundError as e:
            logger.error(f"❌ {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error de formato JSON en config.json: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error inesperado cargando configuración: {e}")
            raise
    
    def _process_config(self, config_obj: Any) -> Any:
        """
        Procesar objeto de configuración y reemplazar variables {{VARIABLE}}
        
        Args:
            config_obj: Objeto de configuración (dict, list, o str)
            
        Returns:
            Objeto procesado con variables reemplazadas
        """
        if isinstance(config_obj, dict):
            return {key: self._process_config(value) for key, value in config_obj.items()}
        elif isinstance(config_obj, list):
            return [self._process_config(item) for item in config_obj]
        elif isinstance(config_obj, str) and config_obj.startswith('{{') and config_obj.endswith('}}'):
            return self._get_env_variable(config_obj[2:-2].strip())
        else:
            return config_obj
    
    def _get_env_variable(self, var_name: str, default: Any = None) -> Any:
        """
        Obtener variable de entorno y convertir tipos básicos
        
        Args:
            var_name: Nombre de la variable de entorno
            default: Valor por defecto si la variable no existe
            
        Returns:
            Valor de la variable convertido al tipo apropiado
        """
        value = os.getenv(var_name, default)
        
        if value is None:
            logger.warning(f"⚠️ Variable de entorno {var_name} no definida")
            return None
        
        # Conversión de tipos
        if isinstance(value, str):
            # Booleanos
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            # Enteros
            elif value.isdigit():
                return int(value)
            # Flotantes
            elif self._is_float(value):
                return float(value)
            # Listas (separadas por comas)
            elif ',' in value:
                return [item.strip() for item in value.split(',')]
        
        return value
    
    def _is_float(self, value: str) -> bool:
        """Verificar si un string puede convertirse a float"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _validate_config(self):
        """Validar configuración requerida"""
        required_configs = [
            'urls.base_url',
            'paths.shared_folder',
            'analisis.default_parametro', 
            'analisis.default_servicio'
        ]
        
        missing = []
        for config_path in required_configs:
            if self.get(config_path) is None:
                missing.append(config_path)
        
        if missing:
            error_msg = f"❌ Configuración requerida faltante: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("✅ Configuración validada correctamente")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtener valor de configuración usando dot notation
        
        Args:
            key: Llave en formato dot notation (ej: 'urls.base_url')
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor de configuración o default si no existe
        """
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except (KeyError, AttributeError, TypeError):
            return default
    
    def get_all(self) -> Dict[str, Any]:
        """
        Obtener toda la configuración
        
        Returns:
            Diccionario con toda la configuración
        """
        return self.config
    
    def reload(self):
        """Recargar configuración"""
        logger.info("🔄 Recargando configuración...")
        self._initialized = False
        self.__init__()

# Instancia global singleton
config = ConfigLoader()
"""
Módulo de monitoreo de archivos para NOVALYTICS-BOT
Monitoriza una carpeta compartida en busca de nuevos archivos para procesar.
"""

import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable, List, Optional
from datetime import datetime

# Importar configuración
from src.core import settings

logger = logging.getLogger(__name__)

class FileHandler(FileSystemEventHandler):
    """
    Manejador de eventos de archivos para Watchdog.
    Detecta cuando se crean o modifican archivos en la carpeta monitorizada.
    """
    
    def __init__(self, callback: Callable, allowed_extensions: List[str]):
        """
        Inicializar el manejador de archivos.
        
        Args:
            callback: Función a ejecutar cuando se detecta un archivo válido
            allowed_extensions: Lista de extensiones permitidas
        """
        self.callback = callback
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
        logger.info(f"📁 Manejador inicializado para extensiones: {allowed_extensions}")
    
    def on_created(self, event):
        """
        Se ejecuta cuando se crea un nuevo archivo.
        
        Args:
            event: Evento de sistema de archivos
        """
        if not event.is_directory:
            self._process_file(event.src_path)
    
    def on_modified(self, event):
        """
        Se ejecuta cuando se modifica un archivo existente.
        
        Args:
            event: Evento de sistema de archivos
        """
        if not event.is_directory:
            self._process_file(event.src_path)
    
    def _process_file(self, file_path: str):
        """
        Procesar un archivo detectado.
        
        Args:
            file_path: Ruta del archivo a procesar
        """
        try:
            file = Path(file_path)
            
            # Verificar que el archivo existe y no está vacío
            if not file.exists() or file.stat().st_size == 0:
                return
            
            # Verificar extensión permitida
            if not self._is_extension_allowed(file.suffix):
                return
            
            # Verificar tamaño máximo
            if not self._is_size_within_limit(file):
                return
            
            # Esperar a que el archivo termine de copiarse
            if self._is_file_locked(file):
                logger.info(f"⏳ Archivo en uso, esperando: {file.name}")
                return
            
            logger.info(f"📁 Archivo detectado: {file.name} ({file.stat().st_size} bytes)")
            
            # Ejecutar callback con el archivo
            self.callback(file)
            
        except Exception as e:
            logger.error(f"❌ Error procesando archivo {file_path}: {e}")
    
    def _is_extension_allowed(self, extension: str) -> bool:
        """
        Verificar si la extensión del archivo está permitida.
        
        Args:
            extension: Extensión del archivo (ej: '.xlsx')
            
        Returns:
            bool: True si la extensión está permitida
        """
        extension_lower = extension.lower()
        is_allowed = extension_lower in self.allowed_extensions
        
        if not is_allowed:
            logger.debug(f"📌 Extensión no permitida: {extension}")
        
        return is_allowed
    
    def _is_size_within_limit(self, file: Path) -> bool:
        """
        Verificar si el archivo está dentro del límite de tamaño.
        
        Args:
            file: Objeto Path del archivo
            
        Returns:
            bool: True si el tamaño está dentro del límite
        """
        max_size_mb = settings.max_file_size_mb
        file_size_mb = file.stat().st_size / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            logger.warning(f"⚠️ Archivo demasiado grande: {file.name} ({file_size_mb:.2f} MB > {max_size_mb} MB)")
            return False
        
        return True
    
    def _is_file_locked(self, file: Path, max_attempts: int = 5, delay: float = 1.0) -> bool:
        """
        Verificar si el archivo está bloqueado (siendo copiado).
        
        Args:
            file: Objeto Path del archivo
            max_attempts: Intentos máximos de verificación
            delay: Delay entre intentos en segundos
            
        Returns:
            bool: True si el archivo está bloqueado
        """
        for attempt in range(max_attempts):
            try:
                # Intentar abrir el archivo en modo lectura
                with open(file, 'rb'):
                    pass
                return False  # Archivo accessible
            except (IOError, PermissionError):
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                else:
                    return True  # Archivo aún bloqueado después de intentos
        
        return True

class FileMonitor:
    """
    Monitor de carpeta compartida para detectar nuevos archivos.
    """
    
    def __init__(self):
        """Inicializar el monitor de archivos."""
        self.observer = None
        self.is_monitoring = False
        self.callback = None
        
        # Configuración desde settings
        self.monitor_folder = settings.shared_folder
        self.allowed_extensions = settings.monitoring_allowed_extensions
        self.check_interval = settings.monitoring_interval_seconds
        
        logger.info(f"📋 Configuración de monitoreo:")
        logger.info(f"   📁 Carpeta: {self.monitor_folder}")
        logger.info(f"   📝 Extensiones: {self.allowed_extensions}")
        logger.info(f"   ⏰ Intervalo: {self.check_interval}s")
    
    def start(self, callback: Callable[[Path], None]):
        """
        Iniciar el monitoreo de la carpeta.
        
        Args:
            callback: Función a ejecutar cuando se detecta un archivo válido
            
        Returns:
            bool: True si el monitoreo se inició correctamente
        """
        try:
            # Verificar que la carpeta existe
            if not self.monitor_folder.exists():
                logger.error(f"❌ Carpeta no existe: {self.monitor_folder}")
                return False
            
            self.callback = callback
            
            # Crear observer y manejador
            self.observer = Observer()
            event_handler = FileHandler(self._handle_file, self.allowed_extensions)
            
            # Programar el observer
            self.observer.schedule(
                event_handler,
                str(self.monitor_folder),
                recursive=False  # No monitorear subcarpetas
            )
            
            # Iniciar el observer
            self.observer.start()
            self.is_monitoring = True
            
            logger.info(f"🚀 Monitoreo iniciado en: {self.monitor_folder}")
            logger.info("👀 Esperando nuevos archivos...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando monitoreo: {e}")
            return False
    
    def stop(self):
        """Detener el monitoreo."""
        if self.observer and self.is_monitoring:
            self.observer.stop()
            self.observer.join()
            self.is_monitoring = False
            logger.info("⏹️ Monitoreo detenido")
    
    def _handle_file(self, file_path: Path):
        """
        Manejar archivo detectado (ejecutar callback).
        
        Args:
            file_path: Ruta del archivo detectado
        """
        try:
            if self.callback:
                logger.info(f"🎯 Ejecutando callback para: {file_path.name}")
                self.callback(file_path)
            else:
                logger.warning("⚠️ No hay callback configurado para archivos detectados")
                
        except Exception as e:
            logger.error(f"❌ Error en callback para {file_path.name}: {e}")
    
    def run_continuous(self, callback: Callable[[Path], None]):
        """
        Ejecutar monitoreo de forma continua.
        
        Args:
            callback: Función a ejecutar cuando se detecta un archivo
        """
        if not self.start(callback):
            return
        
        try:
            while self.is_monitoring:
                time.sleep(self.check_interval)
                # El monitoreo sigue activo en segundo plano
                
        except KeyboardInterrupt:
            logger.info("⏹️ Monitoreo interrumpido por usuario")
        except Exception as e:
            logger.error(f"❌ Error en monitoreo continuo: {e}")
        finally:
            self.stop()

# Funciones de utilidad para el módulo
def get_file_info(file_path: Path) -> dict:
    """
    Obtener información detallada de un archivo.
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        dict: Información del archivo
    """
    stat = file_path.stat()
    return {
        'name': file_path.name,
        'size': stat.st_size,
        'size_mb': stat.st_size / (1024 * 1024),
        'created': datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'extension': file_path.suffix.lower(),
        'path': str(file_path)
    }

def move_file(source: Path, destination: Path) -> bool:
    """
    Mover archivo a otra ubicación.
    
    Args:
        source: Archivo origen
        destination: Archivo destino
        
    Returns:
        bool: True si se movió correctamente
    """
    try:
        # Crear directorio destino si no existe
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Mover archivo
        source.rename(destination)
        logger.info(f"📦 Archivo movido: {source.name} → {destination}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error moviendo archivo {source.name}: {e}")
        return False

def archive_file(file_path: Path) -> bool:
    """
    Archivar archivo procesado.
    
    Args:
        file_path: Ruta del archivo a archivar
        
    Returns:
        bool: True si se archivó correctamente
    """
    if not settings.move_processed_files:
        logger.info("📌 Archivo procesado (no se mueve por configuración)")
        return True
    
    try:
        # Crear nombre único para el archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        destination = settings.processed_folder / new_name
        
        return move_file(file_path, destination)
        
    except Exception as e:
        logger.error(f"❌ Error archivando archivo {file_path.name}: {e}")
        return False

# Función principal para uso externo
def start_file_monitoring(processing_callback: Callable[[Path], None]):
    """
    Iniciar monitoreo de archivos (función principal para otros módulos).
    
    Args:
        processing_callback: Función que procesa los archivos detectados
    """
    monitor = FileMonitor()
    
    def wrapped_callback(file_path: Path):
        """
        Callback wrapper con manejo de errores y archivado.
        """
        try:
            # Procesar archivo
            processing_callback(file_path)
            
            # Archivar después de procesar
            if settings.move_processed_files:
                archive_file(file_path)
            elif settings.delete_after_processing:
                file_path.unlink()
                logger.info(f"🗑️ Archivo eliminado: {file_path.name}")
                
        except Exception as e:
            logger.error(f"❌ Error procesando archivo {file_path.name}: {e}")
    
    # Iniciar monitoreo continuo
    monitor.run_continuous(wrapped_callback)
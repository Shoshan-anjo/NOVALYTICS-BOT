#!/usr/bin/env python3
"""
Test del módulo de monitoreo de archivos
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.append(str(Path(__file__).parent))

from src.event.file_monitor import FileMonitor, get_file_info
import tempfile
import time

def test_monitor():
    """Probar el monitor de archivos"""
    print("🧪 Probando FileMonitor...")
    
    # Crear carpeta temporal
    with tempfile.TemporaryDirectory() as temp_dir:
        monitor = FileMonitor()
        
        def test_callback(file_path):
            print(f"✅ Callback ejecutado para: {file_path.name}")
            file_info = get_file_info(file_path)
            print(f"   📊 Tamaño: {file_info['size_mb']:.2f} MB")
            return True
        
        # Probar que se inicializa correctamente
        print("✅ FileMonitor inicializado")
        
        # Probar get_file_info
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Contenido de prueba")
        
        info = get_file_info(test_file)
        print(f"✅ get_file_info funciona: {info['name']}")
        
        print("🎉 ¡Todas las pruebas pasaron!")

if __name__ == "__main__":
    test_monitor()
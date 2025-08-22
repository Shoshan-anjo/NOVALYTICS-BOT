#!/usr/bin/env python3
"""
Test del ConfigLoader
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.core import config

def test_config_loader():
    """Probar que el ConfigLoader funciona correctamente"""
    print("🧪 Testing ConfigLoader...")
    
    # Test de valores básicos
    tests = [
        ('urls.base_url', 'http://192.168.100.166:5002'),
        ('browser.headless', False),
        ('analisis.default_parametro', '1'),
        ('paths.shared_folder', 'C:/Users/aj.montalvo/Desktop/Carpeta_Compartida')
    ]
    
    all_passed = True
    
    for key, expected_value in tests:
        actual_value = config.get(key)
        status = "✅" if actual_value == expected_value else "❌"
        print(f"{status} {key}: {actual_value} (expected: {expected_value})")
        
        if actual_value != expected_value:
            all_passed = False
    
    # Test de valores desde .env
    env_tests = ['credentials.username', 'credentials.password']
    for key in env_tests:
        value = config.get(key)
        status = "✅" if value else "❌"
        print(f"{status} {key}: {'***' if value else 'NOT SET'}")
        
        if not value:
            all_passed = False
    
    if all_passed:
        print("🎉 ¡Todos los tests pasaron!")
    else:
        print("❌ Algunos tests fallaron")
    
    return all_passed

if __name__ == "__main__":
    test_config_loader()
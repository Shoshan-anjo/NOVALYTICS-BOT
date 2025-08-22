#!/usr/bin/env python3
"""
Test del módulo settings.py
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.core import settings

def test_settings():
    """Probar que settings funciona correctamente"""
    print("🧪 Testing Settings...")
    
    # Test de properties básicas
    tests = [
        ('app_name', 'NOVALYTICS-BOT'),
        ('base_url', 'http://192.168.100.166:5002'),
        ('browser_headless', False),
        ('default_parametro', '1'),
    ]
    
    all_passed = True
    
    for property_name, expected_value in tests:
        actual_value = getattr(settings, property_name)
        status = "✅" if actual_value == expected_value else "❌"
        print(f"{status} {property_name}: {actual_value} (expected: {expected_value})")
        
        if actual_value != expected_value:
            all_passed = False
    
    # Test de paths
    paths_to_test = [
        'shared_folder',
        'downloads_folder', 
        'uploads_folder',
        'logs_folder'
    ]
    
    for path_name in paths_to_test:
        path = getattr(settings, path_name)
        status = "✅" if path else "❌"
        print(f"{status} {path_name}: {path}")
        
        if not path:
            all_passed = False
    
    # Test de métodos
    print(f"✅ is_development: {settings.is_development()}")
    print(f"✅ is_production: {settings.is_production()}")
    
    # Test browser config
    browser_config = settings.get_browser_config()
    print(f"✅ Browser config: {browser_config}")
    
    if all_passed:
        print("🎉 ¡Todos los tests de Settings pasaron!")
    else:
        print("❌ Algunos tests de Settings fallaron")
    
    return all_passed

if __name__ == "__main__":
    test_settings()
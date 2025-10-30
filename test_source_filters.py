#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar el comportamiento de los filtros de fuentes
"""

print("🧪 INSTRUCCIONES DE PRUEBA")
print("="*50)
print("1. Abre el navegador en: http://localhost:8501")
print("2. Desactiva algunas fuentes (por ejemplo, deja solo 'Ayuntamiento')")
print("3. Cambia la fecha a otro día")
print("4. Verifica que la fuente 'Ayuntamiento' sigue seleccionada")
print("5. Si la fuente no tiene eventos ese día, debería aparecer atenuada pero seguir seleccionada")
print("")
print("✅ COMPORTAMIENTO ESPERADO:")
print("   - Las fuentes seleccionadas se mantienen al cambiar fecha")  
print("   - Si una fuente no tiene eventos, aparece atenuada (0.6 opacidad)")
print("   - Si una fuente no está seleccionada y no tiene eventos, casi invisible (0.3 opacidad)")
print("")
print("❌ COMPORTAMIENTO ANTERIOR (INCORRECTO):")
print("   - Al cambiar fecha se reactivaban todas las fuentes")
print("   - No se conservaba la selección del usuario")
print("")
print("🔧 CAMBIOS REALIZADOS:")
print("   - Eliminado resetSourcesFlag = true al cambiar fecha")
print("   - activeSources se inicializa solo una vez")
print("   - Las fuentes se muestran siempre, con opacidad variable")
print("")
print("Presiona Ctrl+C para salir cuando termines de probar")

try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n👋 Prueba terminada")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

print("🌐 PRUEBA DIRECTA DE ACCESO A IMÁGENES")
print("="*50)

# URLs de prueba
test_urls = [
    "https://larioja.lalistilla.com/wp-content/uploads/2025/10/bolanos.gif",
    "https://admin.lalistilla.com/assets/uploads/planes/plan1758648600.jpg",
    "https://gestion.lalistilla.com/assets/uploads/planes/plan1759222153.jpg"
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

for i, url in enumerate(test_urls):
    print(f"\n--- PRUEBA {i+1} ---")
    print(f"URL: {url}")
    
    try:
        # Intentar con headers normales
        response = requests.get(url, headers=headers, timeout=10, stream=True)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Content-Length: {response.headers.get('content-length', 'N/A')}")
        
        if response.status_code == 200:
            print("✅ Imagen accesible")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - servidor muy lento")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {str(e)[:100]}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de request: {str(e)[:100]}")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)[:100]}")

print(f"\n💡 CONCLUSIÓN:")
print("Si todas las URLs fallan, puede ser:")
print("1. Los servidores de La Listilla están caídos")
print("2. Requieren configuración especial")
print("3. Las URLs han cambiado")
print("4. Bloquean requests automatizados")

print(f"\n🔧 SOLUCIÓN TEMPORAL:")
print("Podemos usar placeholders por categoría para La Listilla")
print("hasta que se resuelvan los problemas de conectividad")
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import re

def conectar_db():
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        return client['prueba3']
    except ConnectionFailure:
        print("\n[!] Error crítico: No se pudo conectar a MongoDB. Revisa que el servicio esté activo.")
        return None

def req1_listar_eventos(db):
    print("\n--- Listado de Eventos (Filtro por Categoría) ---")
    categoria = input("Ingresa una categoría para filtrar (ej. 'charla', o presiona Enter para ver todos): ").strip()
    
    query = {}
    if categoria:
        query = {"categoria": categoria.lower()}
        
    eventos = db.eventos.find(query, {"codigo": 1, "nombre": 1, "fecha": 1, "lugar": 1, "categoria": 1, "_id": 0})
    
    encontrados = False
    for evt in eventos:
        encontrados = True
        print(f"[{evt.get('codigo')}] {evt.get('nombre')} | {evt.get('fecha')} | {evt.get('lugar')} | {evt.get('categoria')}")
    
    if not encontrados:
        print("No se encontraron eventos con esa categoría.")

def req2_filtrar_invitados(db):
    print("\n--- Búsqueda de Invitados (Regex) ---")
    nombre_parcial = input("Ingresa parte del nombre (Enter para omitir): ").strip()
    dominio = input("Ingresa dominio de correo (ej. '@empresa.cl', Enter para omitir): ").strip()
    
    query = {}
    if nombre_parcial:
        query["nombre"] = {"$regex": nombre_parcial, "$options": "i"}
    if dominio:
        dominio_regex = dominio.replace(".", "\.") + "$"
        query["correo"] = {"$regex": dominio_regex}
        
    invitados = db.invitados.find(query, {"_id": 0, "rut": 1, "nombre": 1, "correo": 1})
    for inv in invitados:
        print(f"{inv.get('rut')} - {inv.get('nombre')} - {inv.get('correo')}")

def req3_validar_acceso(db):
    print("\n--- Validar Acceso de Invitado a Evento ($lookup) ---")
    rut = input("Ingresa el RUT del invitado (ej. 11.009.876-3): ").strip()
    cod_evento = input("Ingresa el código del evento (ej. EVT-2025-001): ").strip()
    
    pipeline = [
        {"$match": {"codigo": cod_evento}},
        {"$unwind": "$invitados"},
        {"$match": {"invitados.rut": rut, "invitados.estado": "confirmado"}},
        {"$lookup": {
            "from": "invitados",
            "localField": "invitados.rut",
            "foreignField": "rut",
            "as": "datos_invitado"
        }},
        {"$unwind": "$datos_invitado"},
        {"$project": {
            "_id": 0,
            "evento": "$nombre",
            "rut": "$datos_invitado.rut",
            "nombre": "$datos_invitado.nombre",
            "estado_acceso": "$invitados.estado"
        }}
    ]
    
    resultado = list(db.eventos.aggregate(pipeline))
    if resultado:
        print("\n✅ ACCESO PERMITIDO")
        print(resultado[0])
    else:
        print("\n❌ ACCESO DENEGADO (No existe, no está confirmado o RUT/Evento incorrecto).")

def req4_top_eventos(db):
    print("\n--- Top 3 Eventos con más confirmados ---")
    pipeline = [
        {"$unwind": "$invitados"},
        {"$match": {"invitados.estado": "confirmado"}},
        {"$group": {
            "_id": "$codigo",
            "nombre": {"$first": "$nombre"},
            "total_confirmados": {"$sum": 1}
        }},
        {"$sort": {"total_confirmados": -1}},
        {"$limit": 3}
    ]
    
    top_eventos = db.eventos.aggregate(pipeline)
    for idx, evt in enumerate(top_eventos, 1):
        print(f"{idx}. [{evt['_id']}] {evt['nombre']} - {evt['total_confirmados']} confirmados")

def mostrar_menu():
    print("\n" + "="*40)
    print(" GESTOR DE EVENTOS E INVITADOS")
    print("="*40)
    print("1. Listar eventos")
    print("2. Buscar invitados (Filtros Avanzados)")
    print("3. Validar acceso a evento")
    print("4. Ver Top 3 eventos (Confirmados)")
    print("5. Salir")
    print("="*40)

def main():
    db = conectar_db()
    if db is None:
        return

    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción (1-5): ").strip()
        
        if opcion == '1':
            req1_listar_eventos(db)
        elif opcion == '2':
            req2_filtrar_invitados(db)
        elif opcion == '3':
            req3_validar_acceso(db)
        elif opcion == '4':
            req4_top_eventos(db)
        elif opcion == '5':
            print("Cerrando el sistema... ¡Hasta luego!")
            break
        else:
            print("⚠️ Opción inválida. Por favor, ingresa un número del 1 al 5.")

if __name__ == "__main__":
    main()
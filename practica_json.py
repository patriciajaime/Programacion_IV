import json
mis_datos = '''
{
    "Nombre": "Diego",
    "Edad": 25,
    "Activo": true,
    "Materias": ["python", "APIS", "IA"]
}

'''

datos = json.loads(mis_datos)
print(datos)

json_data_serializacion = json.dumps(datos)

print(json_data_serializacion)
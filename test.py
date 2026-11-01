from fastapi import FastAPI

app = FastAPI()

usuarios = [
            {'id': 1, 'nombre': 'Diego'},
            {'id': 2, 'nombre': 'Ana'},

            ]

@app.get("/")   
def read_root():
    return {'estado': 'bien'}

@app.get("/usuarios")
def get_usuarios():
    return usuarios

@app.post("/usuarios")
def crear_usuario(usuario: dict):
    usuarios.append(usuario)
    return usuario


@app.get("/2")   
def read_root2():
    return {'estado': 'mal'}


@app.get("/3")   
def read_root3():
    return {'estado': 'regular'}

'''
En la terminal de Visual Studio escribir

uvicorn test:app --reload

Abrir el link que se genera en un navegador

http://127.0.0.1:8000/

http://127.0.0.1:8000/docs

http://127.0.0.1:8000/usuarios

'''
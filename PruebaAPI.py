from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def saludar():
    return {"message": "¡Hola, mundo!"}

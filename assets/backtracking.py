from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from assets.backtracking import generate_combinations

app = FastAPI()

# Configurar CORS para permitir solicitudes desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar esto por el dominio del frontend en producción
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/combinations")
def get_combinations():
    json_data = {
        "color": ["red", "blue"],
        "size": ["small", "medium", "large"],
        "shape": ["circle", "square"]
    }
    combinations = generate_combinations(json_data)
    return {"combinations": combinations}

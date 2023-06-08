import uvicorn
from fastapi import FastAPI
import main

uvicorn.run(main.app, host="0.0.0.0", port=8000)

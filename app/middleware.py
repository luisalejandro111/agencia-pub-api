# app/middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time
import os

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls_per_minute=60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = defaultdict(list)
        
    async def dispatch(self, request: Request, call_next):
        # Obtener IP del cliente
        client_ip = request.client.host
        
        # Limpiar solicitudes antiguas
        now = time.time()
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < 60
        ]
        
        # Verificar límite
        if len(self.requests[client_ip]) >= self.calls_per_minute:
            raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Intente en 1 minuto.")
        
        # Registrar solicitud
        self.requests[client_ip].append(now)
        
        # Continuar
        response = await call_next(request)
        return response
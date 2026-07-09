from locust import HttpUser, task, between
import random

class ApiUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def dashboard(self):
        self.client.get("/dashboard")
    
    @task(2)
    def listar_clientes(self):
        self.client.get("/clientes")
    
    @task(1)
    def login(self):
        self.client.post("/login", data={
            "email": "test@test.com",
            "password": "test123"
        })

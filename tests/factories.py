# tests/factories.py
from factory import Factory, Faker, LazyAttribute, Sequence
from factory.alchemy import SQLAlchemyModelFactory
from app.models import Cliente, Empleado, Trabajo, Usuario
import random

# ============================================
# 📌 FÁBRICA CON SESIÓN - Para usar en pruebas
# ============================================
class ClienteFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Cliente
        sqlalchemy_session_persistence = "commit"
        # 👇 IMPORTANTE: La sesión se asigna desde el fixture
    
    tipo_cliente = "natural"
    nombre_razon_social = Faker("name")
    telefono = Faker("phone_number")
    email = Faker("email")
    direccion = Faker("address")
    cedula = Sequence(lambda n: f"V-{10000000 + n}")
    activo = True

class EmpleadoFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Empleado
        sqlalchemy_session_persistence = "commit"
    
    nombre_completo = Faker("name")
    tipo_contrato = "fijo"
    sueldo_fijo = LazyAttribute(lambda _: round(random.uniform(300, 800), 2))
    activo = True

class TrabajoFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Trabajo
        sqlalchemy_session_persistence = "commit"
    
    nombre_trabajo = Faker("sentence", nb_words=3)
    monto_total = LazyAttribute(lambda _: round(random.uniform(100, 5000), 2))
    estado = "pendiente"
    porcentaje_pagado = 0
    # cliente_id se asigna al crear
    # creado_por se asigna al crear
# app/forecasting.py
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

def predecir_consumo(historial: List[Any], 
                    dias_a_predecir: int = 1,
                    min_datos: int = 5,
                    considerar_tendencia: bool = True) -> Optional[Dict[str, Any]]:
    """
    Predice el consumo futuro basado en historial de salidas.
    """
    if not historial or len(historial) < min_datos:
        return None
    
    try:
        datos_validos = []
        for h in historial:
            if hasattr(h, 'fecha') and hasattr(h, 'cantidad_usada'):
                fecha = h.fecha if isinstance(h.fecha, date) else h.fecha.date()
                cantidad = float(h.cantidad_usada) if h.cantidad_usada is not None else 0.0
                if cantidad >= 0:
                    datos_validos.append((fecha, cantidad))
        
        if len(datos_validos) < min_datos:
            return None
            
        datos_validos.sort(key=lambda x: x[0])
        
    except (ValueError, AttributeError, TypeError):
        return None
    
    fechas = [d[0] for d in datos_validos]
    cantidades = np.array([d[1] for d in datos_validos])
    
    promedio_consumo = np.mean(cantidades)
    std_consumo = np.std(cantidades)
    total_dias = (fechas[-1] - fechas[0]).days + 1
    
    if std_consumo < 0.1 * promedio_consumo or not considerar_tendencia:
        prediccion_total = promedio_consumo * dias_a_predecir
        return {
            'prediccion': round(prediccion_total, 2),
            'tipo_modelo': 'promedio_simple',
            'confianza': 0.7 if len(datos_validos) >= 10 else 0.5,
            'consumo_promedio_diario': round(promedio_consumo, 2),
            'dias_analizados': len(datos_validos),
            'rango_fechas': (fechas[0], fechas[-1])
        }
    
    x_dias = np.array([(f - fechas[0]).days for f in fechas]).reshape(-1, 1)
    y_cantidades = cantidades.reshape(-1, 1)
    
    try:
        modelo = LinearRegression()
        modelo.fit(x_dias, y_cantidades)
        
        dias_futuros = np.array([total_dias + i for i in range(dias_a_predecir)]).reshape(-1, 1)
        predicciones_futuras = modelo.predict(dias_futuros)
        
        prediccion_total = max(0, np.sum(np.maximum(predicciones_futuras, 0)))
        r2_score = modelo.score(x_dias, y_cantidades)
        confianza = min(0.95, max(0.3, r2_score))
        
        return {
            'prediccion': round(float(prediccion_total), 2),
            'tipo_modelo': 'regresion_lineal',
            'confianza': round(confianza, 2),
            'consumo_promedio_diario': round(promedio_consumo, 2),
            'tendencia': 'creciente' if modelo.coef_[0][0] > 0 else 'decreciente' if modelo.coef_[0][0] < 0 else 'estable',
            'pendiente_tendencia': round(float(modelo.coef_[0][0]), 4),
            'dias_analizados': len(datos_validos),
            'rango_fechas': (fechas[0], fechas[-1]),
            'predicciones_diarias': [round(float(p[0]), 2) for p in predicciones_futuras]
        }
        
    except Exception:
        prediccion_total = promedio_consumo * dias_a_predecir
        return {
            'prediccion': round(prediccion_total, 2),
            'tipo_modelo': 'promedio_simple_fallback',
            'confianza': 0.4,
            'consumo_promedio_diario': round(promedio_consumo, 2),
            'dias_analizados': len(datos_validos),
            'rango_fechas': (fechas[0], fechas[-1])
        }

def generar_alerta_stock(material_id: int, 
                        stock_actual: float, 
                        historial_consumo: List[Any],
                        dias_anticipacion: int = 3) -> Optional[Dict[str, Any]]:
    """
    Genera alertas proactivas de stock basadas en predicción de demanda.
    """
    prediccion = predecir_consumo(historial_consumo, dias_a_predecir=dias_anticipacion)
    
    if not prediccion:
        return None
    
    consumo_predicho = prediccion['prediccion']
    
    if stock_actual <= consumo_predicho:
        dias_hasta_agotamiento = max(1, int(stock_actual / prediccion['consumo_promedio_diario']))
        fecha_agotamiento = date.today() + timedelta(days=dias_hasta_agotamiento)
        
        return {
            'material_id': material_id,
            'nivel_alerta': 'alta' if stock_actual <= consumo_predicho * 0.5 else 'media',
            'stock_actual': stock_actual,
            'consumo_predicho': consumo_predicho,
            'dias_hasta_agotamiento': dias_hasta_agotamiento,
            'fecha_estimada_agotamiento': fecha_agotamiento,
            'confianza_prediccion': prediccion['confianza'],
            'recomendacion': f"Comprar al menos {round(consumo_predicho * 1.2, 2)} unidades"
        }
    
    return None
# core/risk_manager.py - SISTEMA DE PROTECCIÓN CRÍTICO
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import logging

class RiskManager:
    def __init__(self, mt5_connector):
        self.mt5 = mt5_connector
        self.logger = logging.getLogger('RiskManager')
        
        # CONFIGURACIÓN DE PROTECCIÓN
        self.max_drawdown_percent = 10  # 10% máximo drawdown
        self.auto_close_hour = 15       # 3 PM México (4 PM NY)
        self.max_positions = 8          # Máximo 8 posiciones abiertas

    def verificar_protecciones(self):
        """Verifica todas las protecciones en cada ciclo"""
        try:
            # 1. Verificar horario de mercado
            if self.verificar_cierre_mercado():
                self.cerrar_todas_posiciones()
                return False  # Detener trading
            
            # 2. Verificar drawdown máximo
            if not self.verificar_drawdown_maximo():
                self.cerrar_todas_posiciones()
                return False  # Detener trading
                
            # 3. Verificar número de posiciones
            if not self.verificar_max_posiciones():
                return False  # Esperar sin abrir nuevas
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error en protecciones: {e}")
            return True

    def verificar_cierre_mercado(self):
        """Verifica si es hora de cerrar antes del fin de semana"""
        ahora = datetime.now()
        dia_semana = ahora.weekday()  # 0=Lunes, 4=Viernes
        hora_actual = ahora.hour
        
        # VIERNES después de las 3 PM México = CERRAR TODO
        if dia_semana == 4 and hora_actual >= self.auto_close_hour:
            print("🛑 HORA DE CIERRE - Mercado próximo a cerrar")
            return True
        return False

    def verificar_drawdown_maximo(self):
        """Verifica si el drawdown supera el límite permitido"""
        try:
            account_info = self.mt5.get_account_info()
            if not account_info:
                return True
                
            balance = account_info['balance']
            equity = account_info['equity']
            
            if balance <= 0:
                return True
                
            drawdown_percent = ((balance - equity) / balance) * 100
            
            if drawdown_percent > self.max_drawdown_percent:
                print(f"🚨 DRAWDOWN MÁXIMO SUPERADO: {drawdown_percent:.1f}%")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error verificando drawdown: {e}")
            return True

    def verificar_max_posiciones(self):
        """Verifica no exceder el máximo de posiciones"""
        try:
            positions = mt5.positions_get()
            num_positions = len(positions) if positions else 0
            
            if num_positions >= self.max_positions:
                print(f"⚠️ MÁXIMO DE POSICIONES: {num_positions}/{self.max_positions}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error verificando posiciones: {e}")
            return True

    def cerrar_todas_posiciones(self):
        """Cierra todas las posiciones abiertas"""
        try:
            print("🔔 CERRANDO TODAS LAS POSICIONES...")
            positions = mt5.positions_get()
            
            if not positions:
                print("✅ No hay posiciones abiertas")
                return True
                
            closed_count = 0
            for position in positions:
                if self.cerrar_posicion(position.ticket):
                    closed_count += 1
                    
            print(f"✅ {closed_count} posiciones cerradas")
            return True
            
        except Exception as e:
            print(f"❌ Error cerrando posiciones: {e}")
            return False

    def cerrar_posicion(self, ticket):
        """Cierra una posición específica"""
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False
                
            position = position[0]
            symbol = position.symbol
            volume = position.volume
            position_type = position.type
            
            # Crear orden de cierre opuesta
            if position_type == mt5.ORDER_TYPE_BUY:
                close_type = mt5.ORDER_TYPE_SELL
            else:
                close_type = mt5.ORDER_TYPE_BUY
                
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": close_type,
                "position": ticket,
                "deviation": 20,
                "magic": 234000,
                "comment": "Cierre automático",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Posición {ticket} cerrada")
                return True
            else:
                print(f"❌ Error cerrando posición {ticket}")
                return False
                
        except Exception as e:
            print(f"Error cerrando posición {ticket}: {e}")
            return False

    def aplicar_trailing_stops(self):
        """Aplica trailing stops a posiciones con ganancias"""
        try:
            positions = mt5.positions_get()
            if not positions:
                return
                
            for position in positions:
                profit = position.profit
                current_price = position.price_current
                open_price = position.price_open
                
                # Solo aplicar trailing a posiciones con ganancias
                if profit > 5.00:  # +$5 de profit
                    nuevo_stop = self.calcular_trailing_stop(position)
                    if nuevo_stop:
                        self.modificar_stop_loss(position.ticket, nuevo_stop)
                        
        except Exception as e:
            print(f"Error aplicando trailing stops: {e}")

    def calcular_trailing_stop(self, position):
        """Calcula nuevo stop loss para trailing"""
        try:
            if position.type == mt5.ORDER_TYPE_BUY:
                # Para compras, subir stop loss
                nuevo_stop = position.price_open + 2.0  # +$2 del precio entrada
                if position.sl < nuevo_stop:
                    return nuevo_stop
            else:
                # Para ventas, bajar stop loss  
                nuevo_stop = position.price_open - 2.0  # -$2 del precio entrada
                if position.sl > nuevo_stop:
                    return nuevo_stop
                    
            return None
            
        except Exception as e:
            print(f"Error calculando trailing: {e}")
            return None

    def modificar_stop_loss(self, ticket, new_sl):
        """Modifica el stop loss de una posición"""
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False
                
            position = position[0]
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": new_sl,
                "deviation": 20,
                "magic": 234000,
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"🔄 Trailing stop actualizado: {new_sl:.2f}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error modificando SL: {e}")
            return False
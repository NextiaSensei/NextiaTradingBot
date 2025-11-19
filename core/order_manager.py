import MetaTrader5 as mt5
import logging
from datetime import datetime

class OrderManager:
    def __init__(self, risk_per_trade=0.02):
        self.risk_per_trade = risk_per_trade
        self.logger = logging.getLogger()
    
    def calculate_position_size(self, symbol, stop_loss_pips):
        """Calcular tamaño de posición basado en riesgo"""
        try:
            account_info = mt5.account_info()
            if not account_info:
                return 0.01  # Tamaño mínimo
            
            balance = account_info.balance
            risk_amount = balance * self.risk_per_trade
            
            # Obtener información del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return 0.01
            
            # Calcular valor por pip
            if "JPY" in symbol:
                pip_value = 0.01
            else:
                pip_value = 0.0001
            
            # Calcular tamaño de lote
            lot_size = risk_amount / (stop_loss_pips * pip_value * 100000)
            
            # Ajustar a tamaños válidos
            lot_size = max(lot_size, 0.01)  # Mínimo 0.01 lote
            lot_size = min(lot_size, symbol_info.volume_max)  # Máximo permitido
            
            return round(lot_size, 2)
            
        except Exception as e:
            self.logger.error(f"❌ Error calculando tamaño posición: {e}")
            return 0.01
    
    def send_order(self, symbol, order_type, volume, stop_loss=0, take_profit=0, comment=""):
        """Enviar orden al mercado"""
        try:
            # Definir tipo de orden
            if order_type.upper() == "BUY":
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask
            else:
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            
            # Preparar la orden
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type_mt5,
                "price": price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": 2025,  # Magic number para identificar nuestras órdenes
                "comment": f"NEXTIA-{comment}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Enviar orden
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"❌ Error orden {symbol}: {result.retcode}")
                return False
            else:
                self.logger.info(f"✅ Orden ejecutada: {order_type} {volume} {symbol} - SL: {stop_loss}, TP: {take_profit}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error enviando orden: {e}")
            return False
    
    def close_position(self, ticket):
        """Cerrar posición por ticket"""
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False
            
            position = position[0]
            symbol = position.symbol
            volume = position.volume
            
            # Determinar tipo de orden de cierre
            if position.type == mt5.ORDER_TYPE_BUY:
                close_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            else:
                close_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": symbol,
                "volume": volume,
                "type": close_type,
                "price": price,
                "deviation": 20,
                "magic": 2025,
                "comment": "NEXTIA-CLOSE",
                "type_time": mt5.ORDER_TIME_GTC,
            }
            
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            self.logger.error(f"❌ Error cerrando posición: {e}")
            return False
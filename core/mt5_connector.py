# core/mt5_connector.py - CONEXIÓN ROBUSTA OPTIMIZADA
import MetaTrader5 as mt5
import pandas as pd
import time
import logging
import os
from dotenv import load_dotenv

load_dotenv()

class MT5Connector:
    def __init__(self):
        self.connected = False
        self.logger = logging.getLogger('MT5Connector')
        self.connect()

    def connect(self):
        """Conecta a MT5 con credenciales y reintentos"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not mt5.initialize():
                    print(f"Error inicializando MT5 (intento {attempt + 1})")
                    time.sleep(2)
                    continue

                # Credenciales desde .env
                server = os.getenv('MT5_SERVER', 'RoboForex-Pro')
                login_str = os.getenv('MT5_LOGIN', '68267482')
                password = os.getenv('MT5_PASSWORD', '')
                
                # Convertir login a entero
                try:
                    login = int(login_str)
                except ValueError:
                    print(f"Error: MT5_LOGIN debe ser numero: {login_str}")
                    return False
                
                # Login
                authorized = mt5.login(login, password=password, server=server)
                
                if authorized:
                    self.connected = True
                    print("Conexion MT5 establecida correctamente")
                    return True
                else:
                    print(f"Error en login MT5 (intento {attempt + 1})")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"Error conectando MT5 (intento {attempt + 1}): {e}")
                time.sleep(2)
        
        print("No se pudo conectar a MT5 despues de varios intentos")
        return False

    def get_account_info(self):
        """Obtiene informacion de la cuenta"""
        if not self.connected:
            return None
            
        try:
            account_info = mt5.account_info()
            if account_info:
                return {
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'margin': account_info.margin,
                    'free_margin': account_info.margin_free,
                    'leverage': account_info.leverage,
                    'currency': account_info.currency
                }
            return None
        except Exception as e:
            print(f"Error obteniendo info cuenta: {e}")
            return None

    def get_error_description(self, retcode):
        """Describe errores de MT5 de forma mas clara"""
        error_messages = {
            10004: "Requote - precio cambiado",
            10006: "Request rechazada", 
            10007: "Orden cancelada",
            10008: "Volumen insuficiente",
            10009: "Sin conexion",
            10010: "Timeout",
            10011: "Orden invalida",
            10012: "Orden invalida",
            10013: "Parametros invalidos",
            10014: "Volumen invalido",
            10015: "Precio invalido",
            10016: "Stop Loss invalido - verifica la distancia",
            10017: "Take Profit invalido",
            10018: "Mercado cerrado",
            10019: "Fondos insuficientes",
            10020: "Orden bloqueada",
            10021: "Limite de ordenes",
            10022: "Cuenta bloqueada", 
            10023: "Trading prohibido",
            10024: "Posicion no encontrada",
            10025: "Orden no encontrada",
            10026: "Limite de posiciones",
            10027: "AutoTrading deshabilitado - ACTIVALO EN MT5",
            10028: "Solo long permitido",
            10029: "Solo short permitido",
            10030: "Simbolo no disponible"
        }
        return error_messages.get(retcode, f"Error desconocido: {retcode}")

    def execute_order(self, symbol, order_type, volume, stop_loss=0, take_profit=0):
        """Ejecuta orden de trading con manejo robusto de errores"""
        if not self.connected:
            return {'success': False, 'error': 'No conectado a MT5'}
            
        try:
            # Obtener precio actual y info del simbolo
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return {'success': False, 'error': f'No se pudo obtener tick para {symbol}'}
            
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return {'success': False, 'error': f'Simbolo {symbol} no disponible'}

            # Verificar que el simbolo este disponible para trading
            if not symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
                return {'success': False, 'error': f'Simbolo {symbol} no disponible para trading'}

            # VERIFICACIONES DE SEGURIDAD MEJORADAS
            if order_type == 'buy':
                price = tick.ask
                # Verificar que stop loss este por debajo del precio actual
                if stop_loss != 0 and stop_loss >= price:
                    return {'success': False, 'error': 'Stop Loss debe estar POR DEBAJO del precio actual para COMPRAS'}
            else:  # sell
                price = tick.bid
                # Verificar que stop loss este por encima del precio actual
                if stop_loss != 0 and stop_loss <= price:
                    return {'success': False, 'error': 'Stop Loss debe estar POR ENCIMA del precio actual para VENTAS'}

            # Verificar take profit valido
            if take_profit != 0:
                if order_type == 'buy' and take_profit <= price:
                    return {'success': False, 'error': 'Take Profit debe estar POR ENCIMA del precio actual para COMPRAS'}
                elif order_type == 'sell' and take_profit >= price:
                    return {'success': False, 'error': 'Take Profit debe estar POR DEBAJO del precio actual para VENTAS'}

            # Preparar orden con parametros optimizados
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": round(volume, 2),  # Redondear a 2 decimales
                "type": mt5.ORDER_TYPE_BUY if order_type == 'buy' else mt5.ORDER_TYPE_SELL,
                "price": price,
                "deviation": 50,  # Aumentado para evitar requotes
                "magic": 234000,  # Magic number unico
                "comment": "NextiaBot-Pro",
                "sl": stop_loss,
                "tp": take_profit,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,  # Mejor ejecucion
            }

            # Enviar orden
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"Orden ejecutada: {symbol} {order_type} {volume} lots")
                return {
                    'success': True,
                    'order_id': result.order,
                    'price': result.price,
                    'volume': result.volume,
                    'sl': stop_loss,
                    'tp': take_profit
                }
            else:
                error_description = self.get_error_description(result.retcode)
                print(f"Error en orden {symbol}: {error_description}")
                return {
                    'success': False,
                    'error': f"{error_description} (Codigo: {result.retcode})",
                    'retcode': result.retcode
                }
                
        except Exception as e:
            error_msg = f"Error ejecutando orden {symbol}: {str(e)}"
            print(f"Error: {error_msg}")
            return {'success': False, 'error': error_msg}

    def check_existing_positions(self, symbol):
        """Verifica si ya hay posiciones abiertas en un simbolo"""
        if not self.connected:
            return False
            
        try:
            positions = mt5.positions_get(symbol=symbol)
            return len(positions) > 0 if positions else False
        except Exception as e:
            print(f"Error verificando posiciones para {symbol}: {e}")
            return False

    def get_open_positions(self):
        """Obtiene todas las posiciones abiertas"""
        if not self.connected:
            return []
            
        try:
            positions = mt5.positions_get()
            return positions if positions else []
        except Exception as e:
            print(f"Error obteniendo posiciones: {e}")
            return []

    def close_position(self, ticket):
        """Cierra una posicion especifica"""
        if not self.connected:
            return False
            
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
                "magic": 234000,
                "comment": "NextiaBot-Close",
                "type_time": mt5.ORDER_TIME_GTC,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"Posicion cerrada: {symbol} (Ticket: {ticket})")
                return True
            else:
                print(f"Error cerrando posicion {ticket}: {result.retcode}")
                return False
                
        except Exception as e:
            print(f"Error cerrando posicion {ticket}: {e}")
            return False

    def get_market_data(self, symbol, timeframe='H1', count=100):
        """Obtiene datos de mercado para analisis"""
        if not self.connected:
            return pd.DataFrame()
            
        try:
            # Mapear timeframe
            tf_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }
            
            mt5_timeframe = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
            
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error obteniendo datos para {symbol}: {e}")
            return pd.DataFrame()

    def shutdown(self):
        """Cierra conexion de forma segura"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Conexion MT5 cerrada")
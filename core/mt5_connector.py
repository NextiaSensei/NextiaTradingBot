import MetaTrader5 as mt5
import pandas as pd
import os
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv

# Cargar variables de entorno DESDE LA RUTA CORRECTA
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

class MT5Connector:
    def __init__(self):
        self.connected = False
        self.mt5 = mt5

    def connect(self):
        """Conectar a MetaTrader 5 usando credenciales del .env"""
        try:
            print("🔌 Inicializando conexión MT5...")
            
            # Inicializar MT5
            if not mt5.initialize():
                print(f"❌ Error inicializando MT5: {mt5.last_error()}")
                print("💡 Asegúrate de que MetaTrader 5 esté ABIERTO")
                return False

            # Credenciales desde variables de entorno - LECTURA CORREGIDA
            server = os.getenv('MT5_SERVER')
            login_str = os.getenv('MT5_LOGIN')
            password = os.getenv('MT5_PASSWORD')
            
            # VERIFICACIÓN EXPLÍCITA DE VARIABLES
            print(f"🔍 DEBUG: Server={server}, Login={login_str}, Password={'*' * len(password) if password else 'None'}")
            
            # Verificar que tenemos credenciales
            if not server or not login_str or not password:
                print("❌ No se encontraron credenciales en el archivo .env")
                print("💡 Verifica que tu archivo config/.env tenga:")
                print("   MT5_SERVER=RoboForex-Pro")
                print("   MT5_LOGIN=68267482") 
                print("   MT5_PASSWORD=JorgeGDS11")
                return False

            # Convertir login a entero
            try:
                login = int(login_str)
            except ValueError:
                print(f"❌ MT5_LOGIN debe ser número: {login_str}")
                return False

            print(f"🔗 Conectando a {server}...")
            print(f"📋 Login: {login}")

            # Login a MT5
            authorized = mt5.login(login, password=password, server=server)

            if authorized:
                account_info = mt5.account_info()
                print("\n" + "="*50)
                print("✅ ✅ ✅ CONEXIÓN EXITOSA ✅ ✅ ✅")
                print("="*50)
                print(f"🏦 Broker: {server}")
                print(f"📊 Cuenta: {login}")
                print(f"💰 Balance: ${account_info.balance:.2f} {account_info.currency}")
                print(f"📈 Equity: ${account_info.equity:.2f} {account_info.currency}")
                print(f"💼 Moneda: {account_info.currency}")
                print(f"🎯 Apalancamiento: 1:{account_info.leverage}")
                print(f"📊 Profit: ${account_info.profit:.2f} {account_info.currency}")
                print("="*50)
                
                self.connected = True
                return True
            else:
                error = mt5.last_error()
                print(f"❌ Error en login: {error}")
                
                # Intentar servidores alternativos de RoboForex
                roboforx_servers = ['RoboForex-Pro', 'RoboForex-Server', 'RoboForexMT5', 'RoboForex-ECN']
                
                for alt_server in roboforx_servers:
                    if alt_server != server:
                        print(f"🔄 Intentando con servidor alternativo: {alt_server}")
                        authorized = mt5.login(login, password=password, server=alt_server)
                        if authorized:
                            account_info = mt5.account_info()
                            print(f"✅ Conexión exitosa con {alt_server}")
                            print(f"💰 Balance: ${account_info.balance:.2f}")
                            self.connected = True
                            return True
                
                print("💡 SOLUCIONES:")
                print("   • Verifica que MetaTrader 5 esté ABIERTO y conectado a RoboForex")
                print("   • En MT5: Tools→Options→Expert Advisors→Allow automated trading")
                print("   • Verifica que el archivo config/.env tenga las credenciales correctas")
                return False
                
        except Exception as e:
            print(f"❌ Error en conexión: {e}")
            return False

    def get_account_info(self):
        """Obtener información de la cuenta"""
        if not self.connected:
            print("❌ No conectado para obtener info de cuenta")
            return None
        return mt5.account_info()

    def get_tick(self, symbol):
        """Obtener tick actual de un símbolo"""
        if not self.connected:
            print(f"❌ No conectado para obtener tick de {symbol}")
            return None
        
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                print(f"❌ Símbolo {symbol} no encontrado")
                return None
            return tick
        except Exception as e:
            print(f"❌ Error obteniendo tick {symbol}: {e}")
            return None

    def get_historical_data(self, symbol, timeframe=mt5.TIMEFRAME_M5, count=100):
        """Obtener datos históricos para análisis técnico"""
        if not self.connected:
            print(f"❌ No conectado para datos históricos de {symbol}")
            return None
        
        try:
            # Verificar si el símbolo está disponible
            if not mt5.symbol_select(symbol, True):
                print(f"❌ No se pudo seleccionar {symbol}")
                return None
            
            # Obtener datos históricos
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                print(f"❌ No se pudieron obtener datos para {symbol}")
                return None
            
            # Convertir a DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            print(f"✅ Datos históricos obtenidos: {symbol} - {len(df)} velas")
            return df
            
        except Exception as e:
            print(f"❌ Error obteniendo datos históricos {symbol}: {e}")
            return None

    def send_order(self, symbol, order_type, volume, sl=0.0, tp=0.0, deviation=20):
        """Enviar orden de trading - VERSIÓN MEJORADA CON MANEJO DE ERRORES"""
        if not self.connected:
            print(f"❌ No conectado para enviar orden en {symbol}")
            return None

        try:
            # Verificar si el símbolo existe
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                print(f"❌ Símbolo {symbol} no existe")
                return None
            
            # Asegurarse de que el símbolo está seleccionado
            if not symbol_info.visible:
                mt5.symbol_select(symbol, True)
                time.sleep(0.1)

            # Obtener tick actual
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                print(f"❌ No se pudo obtener tick para {symbol}")
                return None

            # Definir tipo de orden y precio
            if order_type.upper() == 'BUY':
                trade_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
                if sl > 0: sl = price - sl
                if tp > 0: tp = price + tp
            else:  # SELL
                trade_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
                if sl > 0: sl = price + sl
                if tp > 0: tp = price - tp

            # Preparar la solicitud de orden
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": trade_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": deviation,
                "magic": 2024,
                "comment": "NextiaBot Trade",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Enviar orden
            result = mt5.order_send(request)
            
            # MANEJO MEJORADO DE ERRORES
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ ✅ ORDEN EJECUTADA ✅ ✅")
                print(f"   📊 {symbol} {order_type} {volume} lots")
                print(f"   💰 Precio: {price:.5f}")
                if sl > 0: print(f"   🛑 Stop Loss: {sl:.5f}")
                if tp > 0: print(f"   🎯 Take Profit: {tp:.5f}")
                print(f"   🎫 Ticket: {result.order}")
                return result
                
            elif result.retcode == 10027:  # AutoTrading disabled
                print(f"❌ ERROR CRÍTICO: AutoTrading deshabilitado en MT5")
                print(f"💡 SOLUCIÓN: En MT5 ve a:")
                print(f"   1. Tools → Options → Expert Advisors")
                print(f"   2. Marca 'Allow automated trading'")
                print(f"   3. Marca 'Allow DLL imports'") 
                print(f"   4. Activa el botón 'Auto Trading' (semáforo verde en barra de herramientas)")
                print(f"   5. Haz click en OK y reinicia MT5")
                return result
                
            else:
                print(f"❌ Error en orden {symbol}: {result.retcode}")
                print(f"   💬 {result.comment}")
                
                # Diccionario de errores comunes
                error_messages = {
                    10004: "Requote - precio cambiado",
                    10006: "Request busy", 
                    10007: "Order canceled",
                    10008: "Volume too small",
                    10009: "No money",
                    10014: "Volume too large",
                    10015: "Price incorrect",
                    10016: "Invalid stops",
                    10017: "Trade disabled",
                    10018: "Market closed",
                    10019: "Not enough money",
                    10020: "Price changed",
                    10021: "Invalid order",
                    10022: "Trading timeout",
                    10023: "Invalid order2",
                    10024: "Trade timeout", 
                    10025: "Invalid price",
                    10026: "Invalid stops2",
                    10027: "AutoTrading disabled - ACTIVA AUTO TRADING EN MT5",
                    10028: "No connection to server",
                    10029: "Server error",
                    10030: "Client error",
                    10031: "Timeout",
                    10032: "Not authenticated"
                }
                
                if result.retcode in error_messages:
                    print(f"   📖 Explicación: {error_messages[result.retcode]}")
                
                return result
                
        except Exception as e:
            print(f"❌ Error enviando orden {symbol}: {e}")
            return None

    def get_open_positions(self):
        """Obtener posiciones abiertas"""
        if not self.connected:
            return []
        
        try:
            positions = mt5.positions_get()
            if positions is None:
                return []
            return positions
        except Exception as e:
            print(f"❌ Error obteniendo posiciones: {e}")
            return []

    def close_position(self, ticket):
        """Cerrar una posición específica por ticket"""
        if not self.connected:
            return False
        
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                print(f"❌ Posición {ticket} no encontrada")
                return False
            
            position = position[0]
            symbol = position.symbol
            volume = position.volume
            order_type = position.type
            
            # Determinar precio y tipo de orden para cerrar
            tick = mt5.symbol_info_tick(symbol)
            if order_type == mt5.ORDER_TYPE_BUY:
                close_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                close_type = mt5.ORDER_TYPE_BUY
                price = tick.ask

            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": close_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 2024,
                "comment": "Close NextiaBot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(close_request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Posición cerrada: {symbol} (Ticket: {ticket})")
                return True
            else:
                print(f"❌ Error cerrando posición {ticket}: {result.retcode}")
                return False
                
        except Exception as e:
            print(f"❌ Error cerrando posición {ticket}: {e}")
            return False

    def close_all_positions(self):
        """Cerrar todas las posiciones abiertas"""
        if not self.connected:
            print("❌ No conectado para cerrar posiciones")
            return False
        
        try:
            positions = self.get_open_positions()
            if not positions:
                print("💡 No hay posiciones abiertas para cerrar")
                return True
            
            print(f"🔴 Cerrando {len(positions)} posiciones...")
            success_count = 0
            
            for position in positions:
                if self.close_position(position.ticket):
                    success_count += 1
                time.sleep(0.5)  # Pequeña pausa entre cierres
            
            print(f"✅ {success_count}/{len(positions)} posiciones cerradas")
            return success_count == len(positions)
            
        except Exception as e:
            print(f"❌ Error cerrando todas las posiciones: {e}")
            return False

    def get_symbols_info(self):
        """Obtener información de todos los símbolos disponibles"""
        if not self.connected:
            return []
        
        try:
            symbols = mt5.symbols_get()
            return symbols
        except Exception as e:
            print(f"❌ Error obteniendo símbolos: {e}")
            return []

    def get_server_time(self):
        """Obtener hora del servidor"""
        if not self.connected:
            return None
        
        try:
            return mt5.symbol_info_tick("EURUSD").time
        except:
            return datetime.now()

    def shutdown(self):
        """Cerrar conexión MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("🔴 Conexión MT5 cerrada")

    def print_market_status(self):
        """Imprimir estado del mercado"""
        if not self.connected:
            return
        
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        print(f"\n📊 ESTADO DEL MERCADO - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 50)
        
        for symbol in symbols:
            tick = self.get_tick(symbol)
            if tick:
                spread = (tick.ask - tick.bid) * 10000 if 'JPY' not in symbol else (tick.ask - tick.bid) * 100
                print(f"   {symbol}: Bid {tick.bid:.5f} | Ask {tick.ask:.5f} | Spread {spread:.1f}pips")
            else:
                print(f"   {symbol}: No disponible")
        print("-" * 50)
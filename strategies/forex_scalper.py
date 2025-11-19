import pandas as pd
import numpy as np
from datetime import datetime

class ForexScalper:
    def __init__(self, mt5_connector):
        self.mt5 = mt5_connector
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        print("✅ Forex Scalper inicializado - MODO ACTIVO")

    def calculate_indicators(self, df):
        """Calcular indicadores SIN TA-Lib"""
        try:
            # RSI manual
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # EMA manual
            df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
            
            return df
        except Exception as e:
            print(f"⚠️ Error calculando indicadores: {e}")
            return df

    def analyze_signal(self, symbol):
        """Analizar señal de trading - ESTRATEGIA SIMPLIFICADA PARA PRUEBAS"""
        try:
            # Para PRUEBAS INMEDIATAS, usemos una estrategia simple
            # que genere señales frecuentes para que veas el bot en acción
            
            tick = self.mt5.get_tick(symbol)
            if not tick:
                return None
            
            # ESTRATEGIA DE PRUEBA: Comprar si el último dígito del precio es par, Vender si es impar
            # Esto generará señales frecuentes para que veas el bot funcionando
            last_bid_digit = int(str(tick.bid).replace('.', '')[-1])
            
            if last_bid_digit % 2 == 0:  # Dígito par -> COMPRAR
                return 'BUY'
            else:  # Dígito impar -> VENDER
                return 'SELL'
                
        except Exception as e:
            print(f"⚠️ Error analizando {symbol}: {e}")
            return None

    def execute_trades(self):
        """Ejecutar estrategia de scalping - MODO ACTIVO CON ÓRDENES REALES"""
        print(f"🎯 EJECUTANDO FOREX SCALPER - {datetime.now().strftime('%H:%M:%S')}")
        
        for symbol in self.symbols:
            try:
                # Obtener tick actual
                tick = self.mt5.get_tick(symbol)
                if tick:
                    print(f"   📊 {symbol}: Bid {tick.bid:.5f} | Ask {tick.ask:.5f}")
                
                # Analizar señal
                signal = self.analyze_signal(symbol)
                
                if signal:
                    print(f"   🚦 SEÑAL DETECTADA: {symbol} {signal}")
                    
                    # EJECUTAR ORDEN REAL
                    volume = 0.01  # 0.01 lotes (tamaño pequeño para pruebas)
                    
                    # Enviar orden REAL
                    result = self.mt5.send_order(symbol, signal, volume)
                    
                    if result and hasattr(result, 'retcode') and result.retcode == self.mt5.mt5.TRADE_RETCODE_DONE:
                        print(f"   ✅ ✅ ORDEN EJECUTADA: {signal} {symbol} {volume} lots")
                        print(f"   🎫 Ticket: {result.order}")
                    else:
                        print(f"   ❌ Error en orden: {result}")
                else:
                    print(f"   {symbol}: Sin señal")
                    
            except Exception as e:
                print(f"   ⚠️ Error en {symbol}: {e}")
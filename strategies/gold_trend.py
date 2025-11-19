import MetaTrader5 as mt5
import numpy as np
import pandas as pd

class GoldTrendStrategy:
    def __init__(self, mt5_connector=None):  # ✅ CORREGIDO: Ahora acepta el parámetro
        self.name = "Gold Trend"
        self.timeframe = mt5.TIMEFRAME_H1
        self.symbol = "XAUUSD"
        self.mt5 = mt5_connector  # ✅ Guardamos el connector
    
    def get_data(self, symbol, count=300):
        """Obtener datos de MT5"""
        rates = mt5.copy_rates_from_pos(symbol, self.timeframe, 0, count)
        if rates is None:
            return None
        return pd.DataFrame(rates)
    
    def calculate_atr(self, data, period=14):
        """Calcular Average True Range"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        # Calcular True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        true_range = np.maximum(tr1, np.maximum(tr2, tr3))
        atr = true_range.rolling(period).mean()
        return atr
    
    def analyze(self, symbol=None):
        """Estrategia de tendencia para oro"""
        if symbol is None:
            symbol = self.symbol
            
        data = self.get_data(symbol)
        if data is None or len(data) < 200:
            return None
        
        # Medias móviles para tendencia
        data['sma_50'] = data['close'].rolling(50).mean()
        data['sma_200'] = data['close'].rolling(200).mean()
        data['atr'] = self.calculate_atr(data, 14)
        
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        # Tendencias mejoradas
        trend_up = current['sma_50'] > current['sma_200']
        price_above_sma = current['close'] > current['sma_50']
        momentum_up = current['close'] > prev['close']
        
        # Volatilidad (ATR para stops dinámicos)
        atr_value = current['atr']
        current_price = current['close']
        
        # SEÑAL COMPUESTA
        if trend_up and price_above_sma and momentum_up:
            return {
                'action': 'BUY',
                'symbol': symbol,
                'price': current_price,
                'confidence': 0.75,
                'stop_loss': current_price - (atr_value * 2),
                'take_profit': current_price + (atr_value * 3),
                'strategy': self.name
            }
        elif not trend_up and not price_above_sma and not momentum_up:
            return {
                'action': 'SELL', 
                'symbol': symbol,
                'price': current_price,
                'confidence': 0.75,
                'stop_loss': current_price + (atr_value * 2),
                'take_profit': current_price - (atr_value * 3),
                'strategy': self.name
            }
        
        return None
    
    def execute_trades(self):
        """Ejecutar trading basado en señales"""
        signal = self.analyze()
        if signal:
            print(f"🎯 {self.name}: {signal['action']} {signal['symbol']} "
                  f"| Precio: {signal['price']:.5f} | Conf: {signal['confidence']}")
            # Aquí iría la lógica de ejecución de órdenes
            return signal
        return None
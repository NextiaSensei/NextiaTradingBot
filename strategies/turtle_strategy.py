# strategies/turtle_strategy.py - ESTRATEGIA TURTLE PRO
import pandas as pd
import numpy as np
import MetaTrader5 as mt5

class TurtleStrategy:
    def __init__(self):
        self.symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
        self.name = "Turtle Strategy"

    def get_data(self, symbol, timeframe=mt5.TIMEFRAME_H1, count=100):
        """Obtiene datos históricos"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                return None
            return pd.DataFrame(rates)
        except:
            return None

    def calculate_atr(self, df, period=14):
        """Calcula Average True Range"""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            true_range = np.maximum(tr1, np.maximum(tr2, tr3))
            return true_range.rolling(period).mean()
        except:
            return pd.Series([0] * len(df))

    def analyze(self):
        """Estrategia Turtle mejorada"""
        signals = []
        
        for symbol in self.symbols:
            try:
                df = self.get_data(symbol)
                if df is None or len(df) < 55:
                    continue
                
                # Calcular indicadores
                df['atr'] = self.calculate_atr(df)
                df['highest_20'] = df['high'].rolling(20).max()
                df['lowest_20'] = df['low'].rolling(20).min()
                
                current = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Señal COMPRA - Breakout
                if current['close'] > prev['highest_20']:
                    stop_loss = current['close'] - (current['atr'] * 2)
                    signals.append({
                        'symbol': symbol,
                        'action': 'buy',
                        'stop_loss': stop_loss,
                        'take_profit': current['close'] + (current['atr'] * 3),
                        'confidence': 0.8
                    })
                
                # Señal VENTA - Breakdown
                elif current['close'] < prev['lowest_20']:
                    stop_loss = current['close'] + (current['atr'] * 2)
                    signals.append({
                        'symbol': symbol,
                        'action': 'sell',
                        'stop_loss': stop_loss,
                        'take_profit': current['close'] - (current['atr'] * 3),
                        'confidence': 0.8
                    })
                    
            except Exception as e:
                continue
                
        return signals
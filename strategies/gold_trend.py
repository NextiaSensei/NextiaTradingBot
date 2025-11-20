# strategies/gold_trend.py - ESTRATEGIA ORO MEJORADA
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

class GoldTrendStrategy:
    def __init__(self, mt5_connector=None):
        self.mt5 = mt5_connector
        self.symbol = "XAUUSD"
        self.name = "Gold Trend"

    def get_data(self, count=100):
        """Obtiene datos de oro"""
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, count)
            if rates is None:
                return None
            return pd.DataFrame(rates)
        except:
            return None

    def execute_trades(self):
        """Ejecuta análisis de oro"""
        try:
            df = self.get_data()
            if df is None or len(df) < 50:
                return None
            
            # Medias móviles
            df['sma_50'] = df['close'].rolling(50).mean()
            df['sma_200'] = df['close'].rolling(200).mean()
            
            current = df.iloc[-1]
            
            # Señal basada en tendencia
            if current['sma_50'] > current['sma_200']:
                return {
                    'action': 'BUY',
                    'symbol': self.symbol,
                    'stop_loss': current['close'] - 5.0,  # 5 dólares de stop
                    'take_profit': current['close'] + 8.0, # 8 dólares de take profit
                    'confidence': 0.75
                }
            else:
                return {
                    'action': 'SELL',
                    'symbol': self.symbol, 
                    'stop_loss': current['close'] + 5.0,
                    'take_profit': current['close'] - 8.0,
                    'confidence': 0.75
                }
                
        except Exception as e:
            return None
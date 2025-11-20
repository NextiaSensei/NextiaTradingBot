# strategies/forex_scalper.py - VERSIÓN OPTIMIZADA
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime

class ForexScalper:
    def __init__(self):
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        self.name = "Forex Scalper"
        self.max_trades_per_symbol = 1  # ✅ MÁXIMO 1 OPERACIÓN POR SÍMBOLO
        self.last_trade_time = {}

    def get_data(self, symbol, timeframe=mt5.TIMEFRAME_M5, count=100):
        """Obtiene datos de mercado"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                return None
            return pd.DataFrame(rates)
        except:
            return None

    def has_open_position(self, symbol):
        """Verifica si ya hay posición abierta"""
        try:
            positions = mt5.positions_get(symbol=symbol)
            return len(positions) > 0
        except:
            return False

    def calculate_indicators(self, df):
        """Calcula indicadores técnicos"""
        try:
            # EMA
            df['ema_fast'] = df['close'].ewm(span=8).mean()
            df['ema_slow'] = df['close'].ewm(span=21).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            return df
        except:
            return df

    def calculate_proper_stops(self, symbol, current_price, action):
        """Calcula stops adecuados para cada símbolo"""
        # Para JPY necesitamos stops más grandes
        if 'JPY' in symbol:
            if action == 'buy':
                stop_loss = current_price - 0.30  # 30 pips para JPY
                take_profit = current_price + 0.45  # 45 pips para JPY
            else:
                stop_loss = current_price + 0.30
                take_profit = current_price - 0.45
        else:
            if action == 'buy':
                stop_loss = current_price - 0.0025  # 25 pips
                take_profit = current_price + 0.0035  # 35 pips
            else:
                stop_loss = current_price + 0.0025
                take_profit = current_price - 0.0035
                
        return stop_loss, take_profit

    def analyze(self):
        """Analiza y genera señales con gestión de riesgo"""
        signals = []
        
        for symbol in self.symbols:
            # ✅ VERIFICAR SI YA HAY POSICIÓN ABIERTA
            if self.has_open_position(symbol):
                continue
                
            try:
                df = self.get_data(symbol)
                if df is None or len(df) < 50:
                    continue
                    
                df = self.calculate_indicators(df)
                current = df.iloc[-1]
                
                # ✅ SEÑAL MÁS ESTRICTA - SOLO LAS MEJORES
                buy_condition = (
                    current['ema_fast'] > current['ema_slow'] and 
                    current['rsi'] < 65 and 
                    current['rsi'] > 40  # ✅ EVITAR RSI MUY BAJO
                )
                
                sell_condition = (
                    current['ema_fast'] < current['ema_slow'] and 
                    current['rsi'] > 35 and 
                    current['rsi'] < 60  # ✅ EVITAR RSI MUY ALTO
                )
                
                if buy_condition:
                    stop_loss, take_profit = self.calculate_proper_stops(
                        symbol, current['close'], 'buy'
                    )
                    
                    signals.append({
                        'symbol': symbol,
                        'action': 'buy',
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'confidence': 0.8
                    })
                
                elif sell_condition:
                    stop_loss, take_profit = self.calculate_proper_stops(
                        symbol, current['close'], 'sell'
                    )
                    
                    signals.append({
                        'symbol': symbol,
                        'action': 'sell',
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'confidence': 0.8
                    })
                    
            except Exception as e:
                continue
                
        return signals[:2]  # ✅ MÁXIMO 2 SEÑALES POR CICLO
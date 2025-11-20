# analysis/strategy_analyzer.py - ANALIZA TUS ESTRATEGIAS EXISTENTES
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import MetaTrader5 as mt5
from typing import Dict, List
import logging

class StrategyAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger('StrategyAnalyzer')
    
    def test_strategy_performance(self, strategy_instance, symbol: str, timeframe: str, days: int = 30):
        """Analiza el performance de una estrategia en datos recientes"""
        print(f"\n🔍 ANALIZANDO: {strategy_instance.__class__.__name__} - {symbol} {timeframe}")
        print("-" * 50)
        
        # Obtener datos recientes
        data = self.get_recent_data(symbol, timeframe, days)
        if data.empty:
            print("❌ No se pudieron obtener datos")
            return
            
        # Probar la estrategia en datos recientes
        signals = []
        for i in range(55, len(data)):  # Necesitamos datos suficientes para indicadores
            try:
                current_data = data.iloc[:i+1]
                if hasattr(strategy_instance, 'generate_signals'):
                    strategy_signals = strategy_instance.generate_signals(current_data, symbol)
                else:
                    strategy_signals = strategy_instance.analyze()
                    
                if strategy_signals:
                    signals.extend(strategy_signals)
            except Exception as e:
                continue
                
        # Mostrar resultados
        if signals:
            print(f"✅ Señales generadas: {len(signals)}")
            
            # Analizar tipos de señales
            buy_signals = [s for s in signals if s.get('action') in ['buy', 'BUY']]
            sell_signals = [s for s in signals if s.get('action') in ['sell', 'SELL']]
            
            print(f"   📈 Compras: {len(buy_signals)}")
            print(f"   📉 Ventas: {len(sell_signals)}")
            
            # Verificar calidad de señales
            avg_confidence = np.mean([s.get('confidence', 0.5) for s in signals])
            print(f"   🎯 Confianza promedio: {avg_confidence:.2f}")
            
        else:
            print("❌ No se generaron señales")
            
        return len(signals)
    
    def get_recent_data(self, symbol: str, timeframe: str, days: int) -> pd.DataFrame:
        """Obtiene datos recientes del mercado"""
        try:
            tf_map = {
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4
            }
            
            mt5_timeframe = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
            rates = mt5.copy_rates_from(symbol, mt5_timeframe, datetime.now() - timedelta(days=days), days * 24)
            
            if rates is None:
                return pd.DataFrame()
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos: {e}")
            return pd.DataFrame()

def analyze_current_strategies():
    """Analiza todas tus estrategias actuales"""
    print("🚀 ANALIZANDO ESTRATEGIAS EXISTENTES")
    print("=" * 60)
    
    from strategies.forex_scalper import ForexScalper
    from strategies.turtle_strategy import TurtleStrategy
    from strategies.gold_trend import GoldTrendStrategy
    
    analyzer = StrategyAnalyzer()
    
    # Configuraciones de prueba
    strategies = [
        (ForexScalper(), 'EURUSD', 'M5'),
        (TurtleStrategy(), 'EURUSD', 'H1'),
        (GoldTrendStrategy(), 'XAUUSD', 'H1')
    ]
    
    results = {}
    
    for strategy, symbol, timeframe in strategies:
        signal_count = analyzer.test_strategy_performance(strategy, symbol, timeframe, days=14)
        results[f"{strategy.__class__.__name__}_{symbol}"] = signal_count
        
    # Resumen
    print("\n📊 RESUMEN DE ANÁLISIS:")
    print("-" * 40)
    total_signals = sum(results.values())
    print(f"Señales totales en 14 días: {total_signals}")
    
    if total_signals == 0:
        print("🎯 RECOMENDACIÓN: Las estrategias necesitan ajustes de parámetros")
    elif total_signals < 10:
        print("🎯 RECOMENDACIÓN: Estrategias conservadoras - considerar más pares")
    else:
        print("🎯 RECOMENDACIÓN: Estrategias activas - verificar calidad de señales")

if __name__ == "__main__":
    analyze_current_strategies()
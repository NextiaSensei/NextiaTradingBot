# core/performance_tracker.py
import pandas as pd
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List

class PerformanceTracker:
    def __init__(self):
        self.metrics = {
            'daily_stats': {},
            'weekly_stats': {},
            'strategy_performance': {},
            'risk_metrics': {}
        }
        self.logger = logging.getLogger('PerformanceTracker')
        
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calcula Sharpe Ratio anualizado"""
        if not returns or len(returns) < 2:
            return 0.0
            
        returns_series = pd.Series(returns)
        excess_returns = returns_series - (risk_free_rate / 252)
        return (excess_returns.mean() / returns_series.std()) * (252 ** 0.5)

    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calcula máximo drawdown"""
        if not equity_curve:
            return 0.0
            
        peak = equity_curve[0]
        max_dd = 0.0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
                
        return max_dd * 100  # En porcentaje

    def update_strategy_metrics(self, strategy_name: str, trade_result: Dict):
        """Actualiza métricas por estrategia"""
        if strategy_name not in self.metrics['strategy_performance']:
            self.metrics['strategy_performance'][strategy_name] = {
                'total_trades': 0,
                'winning_trades': 0,
                'total_pnl': 0.0,
                'trade_history': []
            }
        
        strategy_metrics = self.metrics['strategy_performance'][strategy_name]
        strategy_metrics['total_trades'] += 1
        strategy_metrics['total_pnl'] += trade_result['pnl']
        
        if trade_result['pnl'] > 0:
            strategy_metrics['winning_trades'] += 1
            
        strategy_metrics['trade_history'].append({
            'timestamp': datetime.now(),
            'symbol': trade_result['symbol'],
            'pnl': trade_result['pnl'],
            'type': trade_result['type']
        })

    def generate_daily_report(self) -> Dict:
        """Genera reporte diario de performance"""
        today = datetime.now().date()
        
        return {
            'date': today,
            'total_trades': self.metrics.get('total_trades', 0),
            'win_rate': self.calculate_win_rate(),
            'total_pnl': self.metrics.get('total_pnl', 0.0),
            'sharpe_ratio': self.calculate_sharpe_ratio(self.get_daily_returns()),
            'max_drawdown': self.calculate_max_drawdown(self.get_equity_curve())
        }

    def save_metrics(self, filename: str = 'performance_metrics.json'):
        """Guarda métricas en archivo JSON"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.metrics, f, indent=4, default=str)
        except Exception as e:
            self.logger.error(f"Error guardando métricas: {e}")
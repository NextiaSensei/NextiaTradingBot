# main.py - VERSIÓN CON GESTIÓN DE RIESGO MEJORADA
import time
import logging
from datetime import datetime
from core.mt5_connector import MT5Connector
from strategies.forex_scalper import ForexScalper
from strategies.gold_trend import GoldTrendStrategy as GoldTrend
from strategies.turtle_strategy import TurtleStrategy

class NextiaTradingBot:
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('NextiaBot')
        
        self.print_welcome()
        self.mt5 = MT5Connector()
        
        if not self.check_connection():
            return
            
        # Estrategias profesionales
        self.strategies = {
            'scalper': ForexScalper(),
            'gold_trend': GoldTrend(mt5_connector=self.mt5),
            'turtle': TurtleStrategy()
        }
        
        self.performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': 0.0,
            'cycle_count': 0,
            'max_trades_per_cycle': 3  # ✅ MÁXIMO 3 TRADES POR CICLO
        }

    def setup_logging(self):
        """Configura logging profesional"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%H:%M:%S'
        )

    def print_welcome(self):
        """Mensaje de bienvenida profesional"""
        print("\n" + "="*60)
        print("NEXTIA TRADING BOT - SISTEMA PROFESIONAL FOREX")
        print("="*60)
        print("Version: PRO 3.1 | Modo: PRODUCCION SEGURA")
        print("Iniciado:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*60)

    def check_connection(self):
        """Verifica conexión MT5"""
        print("Conectando a MT5...")
        account_info = self.mt5.get_account_info()
        
        if account_info:
            print("\n" + "="*50)
            print("CONEXION EXITOSA")
            print("="*50)
            print(f"Broker: RoboForex-Pro")
            print(f"Cuenta: 68267482")
            print(f"Balance: ${account_info['balance']:.2f} USD")
            print(f"Equity: ${account_info['equity']:.2f} USD")
            print(f"Margen Libre: ${account_info['free_margin']:.2f}")
            print("="*50)
            return True
        else:
            print("ERROR: No se pudo conectar a MT5")
            return False

    def get_open_positions_count(self):
        """Obtiene número de posiciones abiertas"""
        try:
            positions = mt5.positions_get()
            return len(positions) if positions else 0
        except:
            return 0

    def run_trading_cycle(self):
        """Ejecuta ciclo de trading con gestión mejorada"""
        self.performance['cycle_count'] += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        
        print(f"\nCICLO {self.performance['cycle_count']} [{current_time}]")
        print("-" * 40)
        
        # ✅ VERIFICAR POSICIONES ABIERTAS
        open_positions = self.get_open_positions_count()
        print(f"Posiciones abiertas: {open_positions}")
        
        # ✅ SI HAY MUCHAS POSICIONES, ESPERAR
        if open_positions >= 5:
            print("DEMASIADAS POSICIONES - ESPERANDO...")
            return
            
        trades_this_cycle = 0
        
        # Ejecutar estrategias
        for name, strategy in self.strategies.items():
            if trades_this_cycle >= self.performance['max_trades_per_cycle']:
                break
                
            try:
                if name == 'gold_trend':
                    signal = strategy.execute_trades()
                    if signal:
                        print(f"GOLD TREND: {signal['action']} {signal['symbol']}")
                        if self.execute_signal(signal, name):
                            trades_this_cycle += 1
                    else:
                        print(f"GOLD TREND: Sin senal")
                else:
                    signals = strategy.analyze()
                    if signals:
                        print(f"{name.upper()}: {len(signals)} senales")
                        for signal in signals:
                            if trades_this_cycle >= self.performance['max_trades_per_cycle']:
                                break
                            if self.execute_signal(signal, name):
                                trades_this_cycle += 1
                    else:
                        print(f"{name.upper()}: Sin senales")
            except Exception as e:
                print(f"ERROR en {name}: {e}")

    def execute_signal(self, signal, strategy_name):
        """Ejecuta señal de trading con verificación"""
        try:
            if not signal or 'action' not in signal:
                return False
                
            action = signal['action'].lower()
            symbol = signal.get('symbol', 'EURUSD')
            volume = 0.01  # Tamaño fijo para pruebas
            
            # ✅ VERIFICAR STOP LOSS VÁLIDO
            stop_loss = signal.get('stop_loss', 0)
            take_profit = signal.get('take_profit', 0)
            
            if stop_loss == 0:
                print(f"ERROR: Stop Loss invalido para {symbol}")
                return False
            
            print(f"EJECUTANDO: {action.upper()} {symbol} {volume} lots")
            print(f"SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
            
            # Enviar orden
            result = self.mt5.execute_order(
                symbol=symbol,
                order_type=action,
                volume=volume,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if result and result.get('success'):
                self.performance['total_trades'] += 1
                print(f"✅ ORDEN EXITOSA: {result.get('order_id')}")
                return True
            else:
                error_msg = result.get('error', 'Error desconocido')
                print(f"❌ ERROR ORDEN: {error_msg}")
                return False
                
        except Exception as e:
            print(f"❌ Error ejecutando senal: {e}")
            return False

    def print_performance(self):
        """Muestra rendimiento del bot"""
        if self.performance['total_trades'] > 0:
            print(f"\n📊 RESUMEN: {self.performance['total_trades']} trades ejecutados")
            
            # ✅ MOSTRAR POSICIONES ABIERTAS
            open_positions = self.get_open_positions_count()
            account_info = self.mt5.get_account_info()
            
            if account_info:
                profit = account_info['equity'] - account_info['balance']
                profit_color = "🟢" if profit >= 0 else "🔴"
                print(f"{profit_color} Profit Actual: ${profit:.2f}")
                print(f"📈 Posiciones abiertas: {open_positions}")

    def run(self):
        """Ejecuta el bot principal"""
        print("\n🚀 INICIANDO SISTEMA NEXTIA TRADING...")
        print("✅ Bot activo - Modo: GESTIÓN SEGURA")
        print("💡 Máximo 3 trades por ciclo")
        print("💡 Verificación de posiciones activa")
        
        try:
            while True:
                self.run_trading_cycle()
                self.print_performance()
                time.sleep(120)  # ✅ ESPERAR 2 MINUTOS ENTRE CICLOS
                
        except KeyboardInterrupt:
            print("\n🛑 Bot detenido por el usuario")
        except Exception as e:
            print(f"❌ Error critico: {e}")

if __name__ == "__main__":
    bot = NextiaTradingBot()
    bot.run()
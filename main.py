import os
import time
import schedule
from dotenv import load_dotenv
from core.mt5_connector import MT5Connector
from strategies.forex_scalper import ForexScalper
from strategies.gold_trend import GoldTrendStrategy  # NUEVO

# Cargar variables de entorno
load_dotenv()

class NextiaTradingBot:
    def __init__(self):
        self.mt5 = MT5Connector()
        self.forex_scalper = ForexScalper(self.mt5)
        self.gold_trend = GoldTrendStrategy(self.mt5)  # NUEVO

    def start(self):
        """Iniciar el bot de trading"""
        print("🚀 INICIANDO NEXTIA TRADING BOT...")
        
        # Conectar a MT5
        if not self.mt5.connect():
            print("❌ No se pudo conectar a MT5. Saliendo...")
            return

        # Programar estrategias
        schedule.every(1).minutes.do(self.run_scalper)
        schedule.every(5).minutes.do(self.run_gold_trend)  # NUEVO
        schedule.every(5).minutes.do(self.print_status)
        schedule.every().day.at("23:59").do(self.close_all)

        print("✅ Bot iniciado correctamente!")
        print("📊 Estrategias activas: Forex Scalper (M5), Gold Trend (H1)")
        print("⏰ Monitoreando EURUSD, GBPUSD, USDJPY, XAUUSD...")

        # Bucle principal
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🔴 Bot detenido por el usuario")
        finally:
            self.mt5.shutdown()

    def run_scalper(self):
        """Ejecutar scalper cada minuto"""
        self.forex_scalper.execute_trades()

    def run_gold_trend(self):  # NUEVO
        """Ejecutar gold trend cada 5 minutos"""
        self.gold_trend.execute_trades()

    def print_status(self):
        """Imprimir estado cada 5 minutos"""
        account_info = self.mt5.get_account_info()
        if account_info:
            print(f"📈 Status | Balance: ${account_info.balance:.2f} | Equity: ${account_info.equity:.2f}")

    def close_all(self):
        """Cerrar todas las posiciones al final del día"""
        print("🌙 Cerrando operaciones del día...")
        self.mt5.close_all_positions()

if __name__ == "__main__":
    bot = NextiaTradingBot()
    bot.start()
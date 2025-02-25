import socket
import json
import csv
from datetime import datetime
from collections import defaultdict
import numpy as np

class FinanceClient:
    def __init__(self, host, port, window_size=5, initial_capital=100000, order_host="127.0.0.1", order_port=9999):
        self.host = host
        self.port = port
        self.window_size = window_size
        self.price_history = defaultdict(list)
        self.quantity_history = defaultdict(list)
        self.initial_capital = initial_capital
        self.available_capital = initial_capital
        self.portfolio = defaultdict(int)  # Track owned shares
        # Paramètres pour se connecter au serveur d'ordres
        self.order_host = order_host
        self.order_port = order_port

    def calculate_moving_average(self, data_list):
        if len(data_list) >= self.window_size:
            ma = sum(data_list[-self.window_size:]) / self.window_size
            return round(ma, 2)
        return None

    def analyze_sentiment(self, symbol, price, price_ma, volume_signal):
        """Calculate market sentiment on a scale from -100 to 100"""
        if price_ma is None:
            return 0  # Neutral when not enough data

        # Calculate price momentum (percent above/below MA)
        price_momentum = ((price / price_ma) - 1) * 100

        # Volume factor (-25 to 25)
        volume_factor = 0
        if volume_signal == "HIGH":
            volume_factor = 25
        elif volume_signal == "LOW":
            volume_factor = -25

        # Check recent price trend (last 3 periods if available)
        trend_factor = 0
        if len(self.price_history[symbol]) >= 3:
            recent_prices = self.price_history[symbol][-3:]
            if all(recent_prices[i] < recent_prices[i + 1] for i in range(len(recent_prices) - 1)):
                trend_factor = 25  # Consistently rising
            elif all(recent_prices[i] > recent_prices[i + 1] for i in range(len(recent_prices) - 1)):
                trend_factor = -25  # Consistently falling

        # News factor (simplified - using News field if available)
        news_factor = 0

        # Combine factors to get overall sentiment (-100 to 100 scale)
        sentiment = min(100, max(-100, price_momentum + volume_factor + trend_factor + news_factor))
        return round(sentiment, 2)

    def calculate_trade_quantity(self, symbol, price, sentiment, trade_signal):
        """Calculate how many shares to buy or sell based on sentiment"""
        if trade_signal == "WAIT":
            return 0

        # Base quantity calculation (percentage of capital based on sentiment)
        sentiment_weight = abs(sentiment) / 100  # 0 to 1

        # Adjust max_capital_percent based on sentiment strength
        max_capital_percent = min(0.5, 0.1 + (0.4 * sentiment_weight))  # 10% to 50% of capital

        # Calculate maximum quantity based on available capital
        max_investment = self.available_capital * max_capital_percent
        max_quantity = int(max_investment / price)

        # Scale quantity based on sentiment strength
        quantity = int(max_quantity * sentiment_weight)

        # Ensure minimum meaningful trade size
        min_quantity = max(1, int(10000 / price))  # At least $10,000 worth or 1 share
        quantity = max(quantity, min_quantity)

        # For sell orders, can't sell more than we own
        if trade_signal == "SELL":
            quantity = min(quantity, self.portfolio[symbol])

        return quantity

    def analyze_volume(self, quantity, avg_quantity):
        if avg_quantity is None:
            return "NORMAL"
        if quantity > (avg_quantity * 1.5):
            return "HIGH"
        elif quantity < (avg_quantity * 0.5):
            return "LOW"
        return "NORMAL"

    def send_order(self, order_msg):
        """Envoie un message d'ordre au serveur d'ordres."""
        try:
            s_order = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s_order.connect((self.order_host, self.order_port))
            s_order.send((json.dumps(order_msg) + "\n").encode("utf-8"))
            s_order.close()
            print("Order sent:", order_msg)
        except Exception as e:
            print("Error sending order:", e)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        output_file = 'trading_with_sentiment.csv'
        print(f"Data will be saved to: {output_file}")

        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['Timestamp', 'Symbol', 'Price', 'PriceMA', 'Quantity',
                          'Sentiment', 'TradeSignal', 'TradeQuantity', 'Portfolio', 'Capital']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            try:
                sock.connect((self.host, self.port))
                print(f"Connected to {self.host}:{self.port}")

                while True:
                    data = sock.recv(1024).decode()
                    if not data:
                        print("Server closed the connection")
                        break

                    try:
                        message = json.loads(data)
                        symbol = message['Symbol']
                        price = float(message['Price'])
                        market_quantity = int(message['Quantity'])

                        # Update histories
                        self.price_history[symbol].append(price)
                        self.quantity_history[symbol].append(market_quantity)

                        # Calculate Moving Average
                        price_ma = self.calculate_moving_average(self.price_history[symbol])
                        quantity_ma = self.calculate_moving_average(self.quantity_history[symbol])

                        # Analyze market signals
                        volume_signal = self.analyze_volume(market_quantity, quantity_ma)

                        # Determine basic trading signal
                        trade_signal = 'WAIT'
                        if price_ma is not None:
                            if price > price_ma and volume_signal != 'LOW':
                                trade_signal = 'BUY'
                            elif price < price_ma and volume_signal != 'HIGH':
                                trade_signal = 'SELL'

                        # Calculate sentiment
                        sentiment = self.analyze_sentiment(symbol, price, price_ma, volume_signal)

                        # Calculate trade quantity
                        trade_quantity = self.calculate_trade_quantity(symbol, price, sentiment, trade_signal)

                        # Execute trade (simulate)
                        if trade_signal == "BUY" and trade_quantity > 0:
                            cost = price * trade_quantity
                            if cost <= self.available_capital:
                                self.portfolio[symbol] += trade_quantity
                                self.available_capital -= cost
                        elif trade_signal == "SELL" and trade_quantity > 0:
                            self.portfolio[symbol] -= trade_quantity
                            self.available_capital += price * trade_quantity

                        # Create row for CSV
                        row = {
                            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'Symbol': symbol,
                            'Price': price,
                            'PriceMA': price_ma if price_ma is not None else 'Calculating...',
                            'Quantity': market_quantity,
                            'Sentiment': sentiment,
                            'TradeSignal': trade_signal,
                            'TradeQuantity': trade_quantity,
                            'Portfolio': self.portfolio[symbol],
                            'Capital': round(self.available_capital, 2)
                        }

                        # Save to CSV
                        writer.writerow(row)
                        csvfile.flush()

                        # Send order to order server si le signal n'est pas WAIT
                        if trade_signal in ["BUY", "SELL"] and trade_quantity > 0:
                            order_msg = {
                                "Symbol": symbol,
                                "Exchange": "3",  # Valeur constante, à ajuster si nécessaire
                                "Quantity": str(trade_quantity),
                                "Side": "B" if trade_signal == "BUY" else "S",
                                "Price": str(price)
                            }
                            self.send_order(order_msg)

                        # Print analysis
                        print("\n" + "=" * 70)
                        print(f"Stock: {symbol}")
                        print(f"Current Price: ${price:,.2f}")
                        print(
                            f"Price MA ({self.window_size} periods): ${price_ma if price_ma is not None else 'Calculating...'}")
                        print(f"Market Volume: {market_quantity:,} shares")
                        print(f"Market Sentiment: {sentiment:+.2f}")
                        print(f"Trade Signal: {trade_signal}")
                        print(f"Trade Quantity: {trade_quantity:,} shares")
                        print(f"Portfolio: {self.portfolio[symbol]:,} shares")
                        print(f"Available Capital: ${self.available_capital:,.2f}")
                        print("=" * 70)

                    except json.JSONDecodeError:
                        print("Invalid JSON:", data)
                    except Exception as e:
                        print(f"Processing error: {e}")

            except Exception as e:
                print(f"Connection error: {e}")
            finally:
                sock.close()
                print("Connection closed")


if __name__ == "__main__":
    client = FinanceClient("127.0.0.1", 8080, window_size=5, initial_capital=1000000)
    client.run()

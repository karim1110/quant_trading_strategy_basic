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
        
        # Separate volume histories for Buy and Sell orders
        self.buy_volume_history = defaultdict(list)
        self.sell_volume_history = defaultdict(list)
        
        self.order_host = order_host
        self.order_port = order_port
        self.order_socket = None  # Will hold our persistent connection
        self.connect_order_socket()

    def connect_order_socket(self):
        try:
            self.order_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.order_socket.connect((self.order_host, self.order_port))
            print(f"Connected to order server at {self.order_host}:{self.order_port}")
        except Exception as e:
            print("Error connecting to order server:", e)
            self.order_socket = None

    def calculate_moving_average(self, data_list):
        if len(data_list) >= self.window_size:
            ma = sum(data_list[-self.window_size:]) / self.window_size
            return round(ma, 2)
        return None
    
    def analyze_sentiment(self, symbol, price, price_ma, volume_signal, news, buy_volume_ma, sell_volume_ma):
        """Calculate market sentiment on a scale from -100 to 100"""
        if price_ma is None:
            return 0  # Neutral when not enough data

        # Price momentum (percent above/below MA)
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

        # Map the news value (0, 50, 100) to a news factor between -25 and +25.
        try:
            news_value = int(news)
        except ValueError:
            news_value = 50  # Default to neutral if conversion fails
        
        news_value = 0 if news_value == 100 else news_value
        news_value = 100 if news_value == 0 else news_value

        news_factor = (news_value - 50) / 2

        # Incorporate separate buy/sell volume analysis
        if buy_volume_ma is not None and sell_volume_ma is not None and sell_volume_ma != 0:
            ratio = buy_volume_ma / sell_volume_ma
            # Map the ratio such that a ratio > 1 adds a positive adjustment and < 1 adds a negative one.
            volume_ratio_factor = (ratio - 1) * 25  # Scaling factor can be adjusted as needed
        else:
            volume_ratio_factor = 0

        # Combine factors (ensure overall sentiment is within [-100, 100])
        sentiment = min(100, max(-100, price_momentum + volume_factor + trend_factor + news_factor + volume_ratio_factor))
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
        min_quantity = min(1, int(10000 / price))  # At least $10,000 worth or 1 share
        quantity = max(quantity, min_quantity)

        # For sell orders, can't sell more than we own
        if trade_signal == "SELL":
            quantity = min(quantity, self.portfolio[symbol])
        
        if trade_signal == "BUY" and self.available_capital < price * quantity:
            quantity = max(quantity, 10000)

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
        """Send an order message using a persistent socket connection."""
        if self.order_socket is None:
            self.connect_order_socket()
        try:
            self.order_socket.send((json.dumps(order_msg) + "\n").encode("utf-8"))
            print("Order sent:", order_msg)
        except Exception as e:
            print("Error sending order, attempting to reconnect:", e)
            self.order_socket.close()
            self.order_socket = None
            self.connect_order_socket()


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
                        
                        # Update separate volume histories based on order side
                        side = message.get("Side", "B")
                        if side == "B":
                            self.buy_volume_history[symbol].append(market_quantity)
                        elif side == "S":
                            self.sell_volume_history[symbol].append(market_quantity)

                        # Calculate Moving Average for price and overall quantity
                        price_ma = self.calculate_moving_average(self.price_history[symbol])
                        quantity_ma = self.calculate_moving_average(self.quantity_history[symbol])
                        
                        # Calculate Moving Averages for buy and sell volumes
                        buy_volume_ma = self.calculate_moving_average(self.buy_volume_history[symbol])
                        sell_volume_ma = self.calculate_moving_average(self.sell_volume_history[symbol])

                        # Analyze market signals
                        volume_signal = self.analyze_volume(market_quantity, quantity_ma)

                        # Determine basic trading signal
                        trade_signal = 'WAIT'
                        if price_ma is not None:
                            if price > price_ma and volume_signal != 'LOW':
                                trade_signal = 'BUY'
                            elif price < price_ma and volume_signal != 'HIGH':
                                trade_signal = 'SELL'

                        # Calculate sentiment (pass in the buy and sell volume moving averages)
                        news = message.get('News', '50')
                        sentiment = self.analyze_sentiment(symbol, price, price_ma, volume_signal, news, buy_volume_ma, sell_volume_ma)

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

                        # Send order to order server if the signal is not WAIT
                        if trade_signal in ["BUY", "SELL"] and trade_quantity > 0:
                            order_msg = {
                                "Symbol": symbol,
                                "Exchange": "3",  # Adjust as necessary
                                "Quantity": str(trade_quantity),
                                "Side": "B" if trade_signal == "BUY" else "S",
                                "Price": str(price)
                            }
                            self.send_order(order_msg)

                        # Calculate total portfolio value and profit/loss
                        total_portfolio_value = self.available_capital
                        for sym, shares in self.portfolio.items():
                            if self.price_history[sym]:
                                total_portfolio_value += shares * self.price_history[sym][-1]
                        profit_loss = total_portfolio_value - self.initial_capital

                        # Print analysis along with portfolio performance
                        print("\n" + "=" * 70)
                        print(f"Stock: {symbol}")
                        print(f"Current Price: ${price:,.2f}")
                        print(f"Price MA ({self.window_size} periods): ${price_ma if price_ma is not None else 'Calculating...'}")
                        print(f"Market Volume: {market_quantity:,} shares")
                        print(f"Market Sentiment: {sentiment:+.2f}")
                        print(f"Trade Signal: {trade_signal}")
                        print(f"Trade Quantity: {trade_quantity:,} shares")
                        print(f"Portfolio for {symbol}: {self.portfolio[symbol]:,} shares")
                        print(f"Available Capital: ${self.available_capital:,.2f}")
                        print(f"Total Portfolio Value: ${total_portfolio_value:,.2f}")
                        print(f"Profit/Loss: ${profit_loss:,.2f}")
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
    client = FinanceClient("127.0.0.1", 9995, window_size=5, initial_capital=1000000)
    client.run()

# Trading Model Project

The goal of this project is to build a trading model that receives order data and news from 3 different exchanges, processes the information, and then executes trades based on a decision-making algorithm. The project requires implementing a TCP client, maintaining an order book, and creating a trading strategy.

## Data Format

Each order comes in the following JSON format:

```json
{
  "Symbol": "GOOGL",
  "OrderID": "3245",
  "Action": "A",
  "Exchange": "3",
  "Quantity": "148000",
  "News": "0",
  "Side": "S",
  "Description": "Alphabet Class A",
  "Price": "815.34"
}
```

- **Action**: `A` (add to the book) or `M` (modified)
- **Side**: `B` (Buy) or `S` (Sell)
- **Price**: The price at which the buyer/seller is willing to transact
- **Quantity**: The number of shares the buyer/seller is willing to transact

Additionally, news messages are sent alongside orders. For example:

```json
{
  "Symbol": "GOOGL",
  "OrderID": "3245",
  "Action": "A",
  "Exchange": "3",
  "Quantity": "148000",
  "News": "0",
  "Side": "S",
  "Description": "Alphabet Class A",
  "Price": "815.34"
}
```

> **Note:** The news value can vary and may affect the stock price, either causing it to appreciate or depreciate.

## Project Tasks

### Task 1: Data Collection and Model Creation

When connected to port `9995`, you will receive strings in the following JSON format:

```json
{"Symbol": "ESRX", "OrderID": "1136", "Action": "M", "Exchange": "1", "Quantity": "854000", "News": "0", "Side": "B", "Description": "Express Scripts Holding Co", "Price": "69.09"}
{"Symbol": "EXPE", "OrderID": "2237", "Action": "M", "Exchange": "2", "Quantity": "503000", "News": "0", "Side": "S", "Description": "Expedia Inc", "Price": "120.85"}
{"Symbol": "FAST", "OrderID": "1238", "Action": "M", "Exchange": "1", "Quantity": "632000", "News": "0", "Side": "S", "Description": "Fastenal Co", "Price": "49.73"}
{"Symbol": "FB", "OrderID": "3239", "Action": "M", "Exchange": "3", "Quantity": "566000", "News": "50", "Side": "S", "Description": "Facebook", "Price": "133.35"}
{"Symbol": "FISV", "OrderID": "3140", "Action": "M", "Exchange": "3", "Quantity": "467000", "News": "0", "Side": "B", "Description": "Fiserv Inc", "Price": "99.45"}
```

Your objective for Task 1 is to collect this data, create your own model, and analyze the correlation between news and price movements.

### Task 2: Implementing the Trading Model

Implement the model from Task 1 in a TCP client that connects to port `9999`. The client should send back a message containing at least the following keys: `side`, `symbol`, `quantity`, `exchange`, and `price`—which represent your order. An example order message is shown below:

```json
{
  "Symbol": "FISV",
  "Exchange": "3",
  "Quantity": "2000",
  "Side": "B",
  "Price": "99.45"
}
```

## Deliverables

- **Code:** Your implementation of the trading model, including the TCP client, order book, and decision-making algorithm.
- **Presentation:** A 10-minute presentation explaining how you created your model and implemented the system.

> **Note:** You are not expected to find the perfect solution every time. Experimentation and iterative improvements are encouraged.

You are free to implement the system as you see fit, provided that it meets the following requirements:
- Implements a TCP client.
- Maintains an order book.
- Includes a decision-making algorithm.

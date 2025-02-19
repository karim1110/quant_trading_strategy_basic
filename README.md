The goal of this project is to get data from 3 exchanges giving you the orders with the following message:
 
{"Symbol": "GOOGL", "OrderID": "3245", "Action": "A", "Exchange":
"3", "Quantity": "148000", "News": "0", "Side": "S",
"Description": "Alphabet Class A", "Price": "815.34"}
 
Action: A (add to the book) or M (modified) Side: B (Buy) or S (Sell)
Price: price the seller/buyer is ready to pay/sell Quantity: quantity the seller/buyer is ready to pay/sell
 
And to get the news sent at the same time:
 
Task{"Symbol": "GOOGL", "OrderID": "3245", "Action": "A",
"Exchange": "3", "Quantity": "148000", "News": "0", "Side": "S", "Description": "Alphabet Class A", "Price": "815.34"}
 
The news can have many values and can make the stock price appreciate or depreciate.
 
You will try to make money by creating a model and coding a software capable of trading with the exchange.
 
 
Task 1
 
When connected to port 9995, you will receive the following type of string:
 
{"Symbol": "ESRX", "OrderID": "1136", "Action": "M", "Exchange":
"1", "Quantity": "854000", "News": "0", "Side": "B",
"Description": "Express Scripts Holding Co", "Price": "69.09"}
{"Symbol": "EXPE", "OrderID": "2237", "Action": "M", "Exchange":
"2", "Quantity": "503000", "News": "0", "Side": "S",
"Description": "Expedia Inc", "Price": "120.85"}
{"Symbol": "FAST", "OrderID": "1238", "Action": "M", "Exchange":
"1", "Quantity": "632000", "News": "0", "Side": "S",
"Description": "Fastenal Co", "Price": "49.73"}
{"Symbol": "FB", "OrderID": "3239", "Action": "M", "Exchange":
"3", "Quantity": "566000", "News": "50", "Side": "S",
"Description": "Facebook", "Price": "133.35"}
{"Symbol": "FISV", "OrderID": "3140", "Action": "M", "Exchange":
"3", "Quantity": "467000", "News": "0", "Side": "B",
"Description": "Fiserv Inc", "Price": "99.45"}
 
This string is using the JSON format. You will collect this data to create your own model. You will try to correlate news and price.
 
Task 2
Implement this model in a TCP client connecting to port 9999.
 
You will send back a message containing at least the keys: side, symbol, quantity, exchange, and price representing your order.
 
{"Symbol": "FISV", "Exchange": "3", "Quantity": "2000", "Side": "B", "Price": "99.45"}
 
What is expected?
Your code and a presentation to explain how you created your model and you implemented it. A presentation of 10 minutes will be sufficient.
 
You are not expected to find the right answers all the time.
 
You are free to implement a system of your choice however you are required to implement a tcp client, an order book, and a decision-making algorithm.

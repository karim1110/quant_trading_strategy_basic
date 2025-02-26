# train.py
import numpy as np
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


# Train based on synthetic data

N = 1000

# Generate synthetic features:
# Feature 1: price (random between 10 and 500)
prices = np.random.uniform(10, 500, size=N)
# Feature 2: price_ma (price moving average, here taken as price plus small noise)
price_ma = prices + np.random.normal(0, 5, size=N)
# Feature 3: volume_signal factor (-25 for LOW, 0 for NORMAL, 25 for HIGH)
volume_signal = np.random.choice([-25, 0, 25], size=N)
# Feature 4: news value (randomly chosen from 0, 50, or 100)
news = np.random.choice([0, 50, 100], size=N)
# Feature 5: buy_volume_ma (a random number between 100 and 1000)
buy_volume_ma = np.random.uniform(100, 1000, size=N)
# Feature 6: sell_volume_ma (a random number between 100 and 1000)
sell_volume_ma = np.random.uniform(100, 1000, size=N)

# Stack features into one matrix (each row is a sample)
X = np.column_stack((prices, price_ma, volume_signal, news, buy_volume_ma, sell_volume_ma))

# Generate a synthetic target:
# For example, assume that when price > price_ma, the market is bullish (target 1), otherwise bearish (target 0)
y = (prices > price_ma).astype(float)

# Add some noise by flipping 10% of the targets randomly
flip = np.random.rand(N) < 0.1
y[flip] = 1 - y[flip]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create DMatrix objects for XGBoost
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

# Set XGBoost parameters for binary classification
params = {
    'objective': 'binary:logistic',
    'eval_metric': 'logloss',
    'seed': 42
}

# Train the model for a fixed number of rounds
num_boost_round = 50
model = xgb.train(params, dtrain, num_boost_round=num_boost_round)

y_pred_prob = model.predict(dtest)
y_pred = (y_pred_prob > 0.5).astype(int)
acc = accuracy_score(y_test, y_pred)
print(f"Test Accuracy: {acc:.2f}")

joblib.dump(model, "xgb_model.pkl")
print("Model saved to xgb_model.pkl")

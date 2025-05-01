# Trading API Stub

A minimal FastAPI-based server that simulates a basic trading API. This is a dummy implementation intended for testing and development purposes only.

## Features

- Token-based authentication (login/logout)
- Orderbook retrieval (GET)
- Order placement (POST)
- Price streaming via WebSocket

## API Endpoints

### Authentication

- **POST** `/login`: Generate a token
  - Requires username/password
  - Returns JWT token

- **POST** `/logout`: Invalidate token
  - Requires active token

### Order Management

- **GET** `/getorderbook`: Retrieve list of orders
  - Requires authentication
  - Returns a list of orders with ID, action, quantity, symbol

- **POST** `/placeorder`: Place a new order
  - Requires authentication
  - Fields: action, quantity, symbol
  - Returns success status, orderID if successful

### WebSocket

- **WS** `/streamprice`: Stream price data
  - Connect with a list of symbols
  - Receives price updates every second with random values


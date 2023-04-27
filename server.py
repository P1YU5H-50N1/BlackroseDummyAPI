import uvicorn
from fastapi import FastAPI,Body, Depends, Header, WebSocket, WebSocketDisconnect, Request
from typing import Annotated
import asyncio
from model import UserSchema, UserLoginSchema, Order
from auth.auth_handler import signJWT
from auth.auth_bearer import JWTBearer
from auth.blacklist import add_to_blacklist
from utils.tickers import stocks
from sockets import ConnectionManager
import random
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uuid


limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


users = []

websockets_manager = ConnectionManager()

@app.get("/")
@limiter.limit("1/second")
async def index(request:Request):
    return {"health":"Good"}


@app.websocket("/streamprice")
async def websocket_endpoint(websocket: WebSocket, authorization: str = Header(default=None)):
    token = authorization[7:] if authorization else None 
    if not token or not JWTBearer.verify_jwt(token):
        await websocket.accept()
        await websocket.close(code=4000,reason="Invalid Token")
    else: 
        symbols = set()
        await websockets_manager.connect(websocket)

        async def send_messages(symbols,websocket):
            while True:
                await asyncio.sleep(1)
                if len(symbols) > 0:
                    prices = str([(i,random.randint(0,100)) for i in symbols])
                    await websocket.send_text(prices)


        asyncio.create_task(send_messages(symbols,websocket))

        try:
            while True:
                try:
                    data = await websocket.receive_json()
                    print(data)
                    if "symbols" in data:
                        for i in data['symbols']:
                            symbols.add(i)
                except Exception as e:
                    await websocket.send_json({"Status":"Error occured, invalid message"})

        except WebSocketDisconnect:
            await websockets_manager.disconnect(websocket)


@app.get("/getorderbook",dependencies=[Depends(JWTBearer())])
@limiter.limit("1/second")
async def get_order_book(request: Request):
    number_of_orders = random.randint(2,15)
    orders =[
        {
        "orderID":str(uuid.uuid4()),
        "action":random.choice(["BUY","SELL"]),
        "quantity":random.randint(1,90),
        "symbol":random.choice(stocks)
        } for i in range(number_of_orders)
    ]
    return orders

@app.post("/placeorder",dependencies=[Depends(JWTBearer())])
@limiter.limit("1/second")
async def place_order(request:Request,order: Order):
    # Generate fake order ID
    order_id = str(uuid.uuid4())
    success_failure_prob = [True,True,True,True,True,True,False]
    # Create response
    success = random.choice(success_failure_prob)
    if success:
        response = {
            "success": success,
            "orderID": order_id,
            "note": f"{order.action} {order.quantity} shares of {order.symbol} placed"
        }
    else:
        response = {
            "success": success,
            "orderID": None,
            "note": f"{order.action} {order.quantity} shares of {order.symbol}\
                  can't be placed because of margin requirements"
        }       
    return response



@app.post("/user/signup", tags=["user"])
@limiter.limit("1/second")
async def create_user(request:Request, user: UserSchema = Body(...)):
    users.append(user) # replace with db call, making sure to hash the password first
    return signJWT(user.email)

def check_user(data: UserLoginSchema):
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
    return False

@app.post("/user/logout",dependencies=[Depends(JWTBearer())])
@limiter.limit("1/second")
async def logout(request:Request,  authorization: str = Header(default=None)):
    token = authorization[7:]
    add_to_blacklist(token)
    return {"msg":"logged out"}

@app.post("/user/login", tags=["user"])
@limiter.limit("1/second")
async def user_login(request:Request, user: UserLoginSchema = Body(...)):
    if check_user(user):
        return signJWT(user.email)
    return {
        "error": "Wrong login details!"
    }

if __name__ == "__main__":
    uvicorn.run("server:app",reload=True)

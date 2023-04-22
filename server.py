import uvicorn
from fastapi import FastAPI,Body, Depends, Header, WebSocket, WebSocketDisconnect
from typing import Annotated
import asyncio
from model import UserSchema, UserLoginSchema
from auth.auth_handler import signJWT
from auth.auth_bearer import JWTBearer
from auth.blacklist import add_to_blacklist
from sockets import ConnectionManager
import random
app = FastAPI()

users = []

websockets_manager = ConnectionManager()

@app.get("/")
async def index():
    return {"health":"Good"}


@app.websocket("/streamprice")
async def websocket_endpoint(websocket: WebSocket, authorization: Annotated[str | None, Header()] = None):
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


@app.get("/protected",dependencies=[Depends(JWTBearer())])
async def check_protect():
    return {"access":"granted"}

@app.post("/user/signup", tags=["user"])
async def create_user(user: UserSchema = Body(...)):
    users.append(user) # replace with db call, making sure to hash the password first
    return signJWT(user.email)

def check_user(data: UserLoginSchema):
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
    return False

@app.post("/user/logout",dependencies=[Depends(JWTBearer())])
async def logout(authorization: Annotated[str | None, Header()] = None):
    token = authorization[7:]
    add_to_blacklist(token)
    return {"msg":"logged out"}

@app.post("/user/login", tags=["user"])
async def user_login(user: UserLoginSchema = Body(...)):
    if check_user(user):
        return signJWT(user.email)
    return {
        "error": "Wrong login details!"
    }

if __name__ == "__main__":
    uvicorn.run("server:app",reload=True)
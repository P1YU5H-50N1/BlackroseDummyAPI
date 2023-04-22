import uvicorn
from fastapi import FastAPI,Body, Depends, Header, WebSocket, WebSocketDisconnect
from typing import Annotated
from model import UserSchema, UserLoginSchema
from auth.auth_handler import signJWT
from auth.auth_bearer import JWTBearer
from auth.blacklist import add_to_blacklist
from sockets import ConnectionManager

app = FastAPI()

users = []

websockets_manager = ConnectionManager()

@app.get("/")
async def index():
    return {"health":"Good"}


@app.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket, authorization: Annotated[str | None, Header()] = None):
    token = authorization[7:] if authorization else None 
    if not token or not JWTBearer.verify_jwt(token):
        await websocket.accept()
        await websocket.close(code=4000,reason="Invalid Token")
    else: 
        await websockets_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_json()
                print(data)
                await websocket.send_json(data)
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
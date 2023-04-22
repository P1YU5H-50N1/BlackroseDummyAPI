import uvicorn
from fastapi import FastAPI,Body, Depends
from model import UserSchema, UserLoginSchema
from auth.auth_handler import signJWT
from auth.auth_bearer import JWTBearer


app = FastAPI()

users = []

@app.get("/")
async def index():
    return {"health":"Good"}

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

@app.post("/user/login", tags=["user"])
async def user_login(user: UserLoginSchema = Body(...)):
    if check_user(user):
        return signJWT(user.email)
    return {
        "error": "Wrong login details!"
    }

if __name__ == "__main__":
    uvicorn.run("server:app",reload=True)
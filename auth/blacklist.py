from .auth_handler import decodeJWT
import time 

blacklisted_tokens = {
    "tokens":[],
    "expiry_date":{}
}
def token_in_blacklist(jwttoken):
    expired_tokens = []
    blacklisted = False
    for token in blacklisted_tokens["tokens"]:
        if token == jwttoken:
            blacklisted = True
        if time.time() > blacklisted_tokens["expiry_date"][token]:
            expired_tokens.append(token)
            
    for token in expired_tokens:
        del blacklisted_tokens['expiry_date'][token]
        blacklisted_tokens['tokens'].remove(token)
    return blacklisted
        
def add_to_blacklist(token):
    payload = decodeJWT(token)
    blacklisted_tokens["tokens"].append(token)
    blacklisted_tokens["expiry_date"][token] = payload['expires']
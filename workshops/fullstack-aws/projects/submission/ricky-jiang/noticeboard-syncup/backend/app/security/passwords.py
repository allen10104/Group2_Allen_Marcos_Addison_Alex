# This file changes a plain text password into a hashed password that is safe to store

#This is the password hashiing library
import bcrypt

#uses utf-8 encoding to convert the plain text password into bytes, 
# then uses bcrypt to hash the password with a salt, 
# and finally decodes the hashed password back into a string for storage in the database.
def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# used during login. It takes the password someone typed and the hash pulled from the database
# and returns True if they match, False otherwise. It uses bcrypt to compare the two.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
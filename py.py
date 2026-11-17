import secrets

salt = secrets.token_hex(16)
string = "Halo" + salt  

print(string + "Salt : " + salt)
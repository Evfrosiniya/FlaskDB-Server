from flask.ext.mysqldb import MySQL

mysql = MySQL()

responses_codes = [
    {"code": 0, "response": "OK"},
    {"code": 1, "response": "Requested object is not found"},
    {"code": 2, "response": "Invalid request"},
    {"code": 3, "response": "Incorrect request(semantically)"},
    {"code": 4, "response": "Undefined error"},
    {"code": 5, "response": "User/Forum is already exists"}
]
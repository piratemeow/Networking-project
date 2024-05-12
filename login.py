from db import connect_to_db


def login(name,password):
    connection = connect_to_db()
    cursor = connection.cursor()

    # Define the SQL query with placeholders for parameters
    query = "SELECT * FROM user WHERE BINARY name = %s"

    # Define the values to be passed as parameters
    param_values = (name,)

    # Execute the SQL query with parameters
    cursor.execute(query, param_values)

    # Fetch results
    rows = cursor.fetchall()
    print(rows)

    if len(rows) == 0:
        print("Password Incorrect")
        return False
    elif password in rows[0][1]:
        print("Password Correct")
        return True
    else:
        print("Password Incorrect")
        return False

# login("imran","asd")
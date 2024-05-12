import mysql.connector

# Establish connection to MySQL server

def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Hello$",
            database="networking"
        )
        print("Connected to MySQL!")
        return connection

    except mysql.connector.Error as error:
        print("Failed to connect to MySQL:", error)



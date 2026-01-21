import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mahmut.9750",
        database="movie_rating_system"
    )
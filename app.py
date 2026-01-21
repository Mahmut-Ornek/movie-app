from flask import Flask, render_template, request, redirect, url_for
from database_utils import get_db_connection

app = Flask(__name__)

@app.route("/")
def index():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT 
        m.movie_id, m.title, m.release_year, d.director_name,
        GROUP_CONCAT(DISTINCT g.genre_name SEPARATOR ", ") as genres,
        GROUP_CONCAT(DISTINCT CONCAT(a.actor_name, " as ", ma.role) SEPARATOR " | ") as cast_list
        FROM Movie m
        LEFT JOIN Director d ON m.director_id = d.director_id
        LEFT JOIN MovieGenre mg ON m.movie_id = mg.movie_id
        LEFT JOIN Genre g ON mg.genre_id = g.genre_id
        LEFT JOIN MovieActor ma ON m.movie_id = ma.movie_id
        LEFT JOIN Actor a ON ma.actor_id = a.actor_id 
        GROUP BY m.movie_id, m.title, m.release_year, d.director_name
    """
    cursor.execute(query)
    movies = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template("index.html", movies=movies)

@app.route("/rate", methods=["GET", "POST"])
def rate_movie():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        user_id = request.form["user_id"]
        movie_id = request.form["movie_id"]
        score = request.form["score"]

        #backend validation
        if not (1 <= int(score) <= 10):
            return "Error: Score must be between 1 and 10", 400
        
        #insert into table rating
        sql = "INSERT INTO Rating (user_id, movie_id, score) VALUES (%s, %s, %s)"
        cursor.execute(sql, (user_id, movie_id, score))

        db.commit() #save changes to mysql
        cursor.close()
        db.close()
        return redirect(url_for("index"))
    
    cursor.execute("SELECT movie_id, title FROM Movie")
    all_movies = cursor.fetchall()

    cursor.execute("SELECT user_id, username FROM UserAccount")
    all_users = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template("rate.html", movies=all_movies, users=all_users)


@app.route("/delete/<int:movie_id>", methods=["POST"])
def delete_movie(movie_id):
    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("DELETE FROM MovieGenre WHERE movie_id = %s", (movie_id,))
        cursor.execute("DELETE FROM MovieActor WHERE movie_id = %s", (movie_id,))
        cursor.execute("DELETE FROM Rating WHERE movie_id = %s", (movie_id,))
        cursor.execute("DELETE FROM Movie WHERE movie_id = %s", (movie_id,))

        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.rollback() # undo changes if something goes wrong
    finally:
        cursor.close()
        db.close
    
    return redirect(url_for("index"))


@app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
def edit_movie(movie_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        new_title = request.form["title"]
        new_year = request.form["release_year"]
        new_director = request.form["director_id"]

        sql = """
            UPDATE Movie
            SET title = %s, release_year = %s, director_id = %s
            WHERE movie_id = %s
        """
        cursor.execute(sql, (new_title, new_year, new_director, movie_id))
        db.commit()

        cursor.close()
        db.close()
        return redirect(url_for("index"))
    
    cursor.execute("SELECT * FROM Movie WHERE movie_id = %s", (movie_id,))
    movie = cursor.fetchone()

    cursor.execute("SELECT director_id, director_name FROM Director ORDER BY director_name ASC")
    directors = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template("edit.html", movie=movie, directors=directors)


if __name__ == "__main__":
    app.run(debug=True)
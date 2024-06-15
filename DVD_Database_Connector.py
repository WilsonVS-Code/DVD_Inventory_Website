import imdb
import pyodbc
from flask import Flask, render_template


# Connect to your Access database
conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ= C:\Users\Systems\Documents\DVD Database Project\Movie_Database.accdb;')
cursor = conn.cursor()
#  A CODE TO TEST OUT IF THE CONNECTION TO THE DATABASE WAS SUCCESSFUL  
# try:
#     # Establish a connection to your Access database
#     conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ= C:\Users\Systems\Documents\DVD Database Project\Movie_Database.accdb;')
    
#     # If the connection is successful, print a success message
#     print("Connection to the database successful!")

#     # Close the connection
#     conn.close()

# except pyodbc.Error as e:
#     # If there's an error in the connection, print the error message
#     print(f"Error connecting to the database: {e}")



# CODE TO TEST OUT IF THE I HAVE WRITE PERMISSIONS ON THE ACCESS DATABASE
# try:
#     conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ= C:\Users\Systems\Documents\DVD Database Project\Movie_Database.accdb;')
#     cursor = conn.cursor()

#     # Attempt a sample insert operation
#     cursor.execute("INSERT INTO Table1 (Title, Year, Rating, Runtime) VALUES (?, ?, ?, ?)", ('Test', 2022, 7.0, 120))

#     # Commit changes
#     conn.commit()

#     # Close connection
#     conn.close()

#     print("Permission check: Write operation successful. User has write permissions.")

# except pyodbc.Error as e:
#     print(f"Permission check: Error - {e}")
#     print("User might not have sufficient permissions for write operations.")


# Create a cursor to execute SQL commands
# cursor = conn.cursor()

# Inputs 
ia = imdb.IMDb()
movie_name = "The crown and the dragon"
movies = ia.search_movie(movie_name)
barcode = 9327031013863
quantity = 1 

# Function to check if a barcode already exists in the database
def barcode_exists(barcode):
    cursor.execute("SELECT COUNT(*) FROM Movies WHERE Movie_Barcode=?", str(barcode))
    count = cursor.fetchone()[0]
    return count > 0

# Function to Update the access database by increasing qty of existing movies or insert a brand new movie into the database
def insert_or_update_movie_details(barcode, quantity):
    if barcode_exists(barcode):
        # If barcode already exists, update the quantity
        cursor.execute("UPDATE Movies SET Quantity = Quantity + ? WHERE Movie_Barcode=?", quantity, str(barcode))

        # Identifying the Movie from the IMDB API
        movies = ia.search_movie(movie_name)
        movie = movies[0]
        ia.update(movie)

        # The details needed to be inserted in the Copies Table
        title = movie['title']
        status = 'Available'

        #  Inserting initial copies of a particular movie DVD into the Copy Table
        cursor.execute("SELECT Movie_ID FROM Movies WHERE Title = ?", title)
        last_movie_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO Copies (Movie_Title, Status, Movie_Barcode, Movie_ID) VALUES ('{}','{}', {}, {})".format(title, status, barcode, last_movie_id))


    else:  
        # Perform a new search_movie
        movies = ia.search_movie(movie_name)


        if movies:
            movie = movies[0]
            ia.update(movie)
            
            ## WILL 
            # Storing all the required movie details into a list
            movie_details = [{"Title" : movie['title'], "Year" : movie['year'], "Rating" : float(movie['rating']),
                            "Runtime" : int(movie['runtimes'][0]), "Director" : str(movie['director'][0]), "Genre": movie['genre']}]
            
            # Getting all the movie details 
            for i in movie_details:

                title = i.get('Title', '')
                year = i.get('Year', '')
                director = i.get('Director', '')
                rating = i.get('Rating', '')
                runtime = i.get('Runtime', '')
                status = 'Available'
    

                # Inserting the specified movie details into the respectiove tables in access database
                cursor.execute("INSERT INTO Movies (Title, Release_Year, Director, Rating, Duration, Quantity, Movie_Barcode) VALUES ('{}', {}, '{}', {}, {}, {}, {})"
                               .format(title, year, director, rating, runtime, quantity, barcode))
                
                # Inserting the movie details into the Copies table (Keep track of availability) in the access database 
                cursor.execute("SELECT Movie_ID FROM Movies WHERE Title = ?", title)
                last_movie_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO Copies (Movie_Title, Status, Movie_Barcode, Movie_ID) VALUES ('{}','{}', {}, {})".format(title, status, barcode, last_movie_id))


                # Inserting different types of genres into the Genre table in access database
                Genre_list = movie['genres']

                # Check if the genre is already in the database
                for genre_type in Genre_list:
                    cursor.execute("SELECT COUNT(*) FROM Genres WHERE Genre_Type=?", genre_type)
                    genre_counter = cursor.fetchone()[0]
                    # 0 means the genre is not in the database, so we have to insert it
                    if genre_counter == 0:
                        cursor.execute("INSERT INTO Genres (Genre_Type) VALUES (?)", (genre_type,))
                    
                    ###!!! conjunction table to match the different genres to different movies 
                    # cursor.execute("SELECT Movie_ID FROM Movies WHERE Title = ?", title)
                    # cursor.execute("SELECT Genre_ID FROM Genres WHERE ")
                    # cursor.execute("INSERT INTO MovieGenre (Movie_ID, Genre_ID) VALUES ({}, {})".format(last_movie_id, ))
                # Keeping record of the Genres associated to each Movies



# Call Out the functions 
insert_or_update_movie_details(barcode, quantity)
barcode_exists(barcode)

conn.close()

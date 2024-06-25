# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import date, timedelta
import imdb
import pyodbc
import random
import string

app = Flask(__name__, static_url_path ='/static')

# Set a secret key for the application
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Replace DATABASE_CONNECTION_STRING with your actual connection string
conn_str = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ= C:\Users\Systems\Documents\DVD_Inventory_Website\Movie_Database.accdb;'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()


# ROUTES 
# Routes for Login Purposes 
# The ROOT URL (need this to initiate the whole website) represented by ('/')
@app.route('/')
def index():
    error_message = request.args.get('error_message', '')
    return render_template('login.html', error_message=error_message)
    
    
# Retrieving Username and Password Inputs and Checking with the Database before moving to the next page.
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Check if the provided username and password match in the Access database
    cursor.execute("SELECT * FROM Staff WHERE Staff_Username = ? AND Staff_Password = ?",username, password)
    user = cursor.fetchone()

    if user:
    # Successful login, redirect to a new page or perform additional actions
        # The Name of the user is located at the second column of the Users table (index 1)
        session['user_name'] = user[1]
        return redirect(url_for('dashboard'))
    else:
        # Invalid credentials, redirect back to the login page with an error message
        error_message = 'Invalid Username and/or Password!'
        return redirect(url_for('index', error_message=error_message))


# Defining the structure of the Movie Table (The structure in the database)
class Movie:
    def __init__(self, Movie_ID, Title, Release_Year, Director, Rating, Duration, Quantity, Movie_Barcode):
        self.Movie_ID = Movie_ID
        self.Title = Title
        self.Release_Year = Release_Year
        self.Director = Director
        self.Rating = Rating 
        self.Duration = Duration
        self.Quantity = Quantity
        self.Movie_Barcode = Movie_Barcode


# The Menu where the appropriate users can have access to.
@app.route('/dashboard')
def dashboard():
    # Retrieve the users name from the session
    user_name = session.get('user_name')

    # Retrieve movie details from the database
    cursor.execute("SELECT * FROM Movies")
    movies = [Movie(*row) for row in cursor.fetchall()]

    return render_template('dashboard.html', user_name=user_name, movies=movies)

# The route for Searching up Movie details from the database.
@app.route('/search_movies', methods=['GET'])
def search_movies():

    # Retrieve the users name from the session
    user_name = session.get('user_name')

    search_query = request.args.get('search_query', '')

    if search_query.isdigit():
        # Execute a search query on the database (If Movie barcode is used)
        cursor.execute("SELECT * FROM Movies WHERE Movie_Barcode = ?", (search_query,))
    else:
        # Exceute a search query on the database (if Movie name is used)
        cursor.execute("SELECT * FROM Movies WHERE Title LIKE ?", '%' + search_query + '%')


    search_results = [Movie(*row) for row in cursor.fetchall()]
    # Render the template with the search results
    return render_template('dashboard.html', user_name = user_name, movies=search_results)

# Define route for the "Add New Movie" page
@app.route('/add_movie')
def add_movie():
    return render_template('add_movie.html')


# Define route to handle form submission for adding a new movie
@app.route('/add_movie', methods=['POST'])
def add_movie_post():
    # Retrieve form data
    movie_name = request.form.get('movie_name')
    movie_barcode = request.form.get('movie_barcode')

    # Extract movie details from IMDb
    movie_details = insert_or_update_movie_details(movie_barcode, movie_name)

    # Render template with movie details
    return render_template('add_movie.html', 
                           movie_details=movie_details, 
                           movie_barcode=movie_barcode)


# Define route for the "Add New Customer" page
@app.route('/add_customer')
def add_customer():
    return render_template('add_customer.html')


# Define route to handle form submission for adding a new customer 
@app.route('/add_customer', methods=['POST'])
def add_customer_post():
    if request.method == 'POST':
        # Extract customer details from form submission
        Customer_FirstName = request.form.get('Customer_FirstName')
        Customer_LastName = request.form.get('Customer_LastName')
        Customer_Email = request.form.get('Customer_Email')
        Customer_PhoneNumber = request.form.get('Customer_PhoneNumber')
        Customer_Address = request.form.get('Customer_Address')


        # Generate a secure password
        Customer_Password = generate_password()

        # Insert customer details into the database, including the password
        # Remember to hash the password before storing it in the database
        import hashlib
        hashed_password = hashlib.sha256(Customer_Password.encode()).hexdigest()  # Example hash with SHA-256

        # Insert customer details into the database
        cursor.execute("INSERT INTO Customer (Customer_FirstName, Customer_LastName, Customer_Email, Customer_PhoneNumber, Customer_Address, Customer_Password) VALUES (?, ?, ?, ?, ?, ?)", 
                       (Customer_FirstName, Customer_LastName, Customer_Email, Customer_PhoneNumber, Customer_Address, hashed_password))
        conn.commit()

        # Flash a success message
        flash("Customer details added successfully!", "success")

        return redirect(url_for('add_customer'))

    # Render the HTML template for adding customer details
    return render_template('add_customer.html', 
                           Customer_FirstName=Customer_FirstName, 
                           Customer_LastName = Customer_LastName, 
                           Customer_Email = Customer_Email,
                           Customer_PhoneNumber = Customer_PhoneNumber,
                           Customer_Address = Customer_Address)

    # Define route for the "Add New Staff" page
@app.route('/add_staff')
def add_staff():
    return render_template('add_staff.html')


# Define route to handle form submission for adding a new staff
@app.route('/add_staff', methods=['POST'])
def add_staff_post():
    if request.method == 'POST':
        # Extract staff details from form submission
        Staff_FirstName = request.form.get('Staff_FirstName')
        Staff_LastName = request.form.get('Staff_LastName')
        Staff_Username = request.form.get('Staff_Username')
        Staff_Password = request.form.get('Staff_Password')

        # Insert staff details into the database
        cursor.execute("INSERT INTO Staff (Staff_FirstName, Staff_LastName, Staff_Username, Staff_Password) VALUES (?, ?, ?, ?)", 
                       (Staff_FirstName, Staff_LastName, Staff_Username, Staff_Password))
        conn.commit()

        # Flash a success message
        flash("Staff details added successfully!", "success")

        return redirect(url_for('add_staff'))

    # Render the HTML template for adding staff details
    return render_template('add_staff.html')

# Gets the Customers details based on the input (Phone Number)
# Handles customer identification and initial form rendering.
@app.route('/get_customer_details', methods=['GET', 'POST'])
def get_customer_details():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        print("Received phone number:", phone_number)  # Debugging statement

        # Fetch customer details by phone number
        cursor.execute("SELECT Customer_ID, Customer_FirstName, Customer_LastName FROM Customers WHERE Customer_PhoneNumber = ?", (phone_number,))
        customer = cursor.fetchone()
        print("Fetched customer details:", customer)  # Debugging statement
        
        if customer:
            session.clear()  # Clear session data
            # Store customer details in session for further use
            session['customer_id'] = customer[0]  # Access tuple elements by index
            session['customer_name'] = f"{customer[1]} {customer[2]}"

            # Get the current date
            rent_date = date.today().strftime("%Y-%m-%d")

            # Render the page with customer details
            return render_template('get_customer_details.html', 
                                   customer_id=session['customer_id'], 
                                   customer_name=session['customer_name'],
                                   rent_date=rent_date)
    
        else:
            # If customer not found, display a message or handle the error
            return render_template('get_customer_details.html', error="Customer not found")
    
    # For GET request, just render the template without any data
    return render_template('get_customer_details.html')



@app.route('/scan_movie', methods=['POST'])
def scan_movie():
    barcode = request.form.get('barcode')
    print("Received barcode:", barcode)  # Debugging statement

    try:
        # Fetch movie details
        cursor.execute("SELECT Movie_ID, Title FROM Movies WHERE Movie_Barcode = ?", (barcode,))
        movie = cursor.fetchone()
        print("Fetched movie details:", movie)  # Debugging statement

        if not movie:
            return jsonify({'error': 'Movie not found'})

        movie_id = movie.Movie_ID
        movie_title = movie.Title

        # Check inventory availability
        cursor.execute("SELECT Inventory_Availability FROM Inventory WHERE Movie_ID = ?", (movie_id,))
        inventory = cursor.fetchone()
        if not inventory or inventory.Inventory_Availability <= 0:
            return jsonify({'error': 'Movie is fully RENTED OUT'})

        # Update inventory availability
        new_availability = inventory.Inventory_Availability - 1
        cursor.execute("UPDATE Inventory SET Inventory_Availability = ? WHERE Movie_ID = ?", (new_availability, movie_id))
        conn.commit()

        rent_date = date.today()
        return_date = rent_date + timedelta(weeks=1)

        if 'rented_movies' not in session:
            session['rented_movies'] = []

        # Check if the movie is already in the rented_movies list
        movie_found = False
        for rented_movie in session['rented_movies']:
            if rented_movie['movie_id'] == movie_id:
                rented_movie['quantity'] += 1
                movie_found = True
                break

        if not movie_found:
            session['rented_movies'].append({
                'movie_id': movie_id,
                'movie_title': movie_title,
                'rent_date': rent_date.strftime("%Y-%m-%d"),
                'return_date': return_date.strftime("%Y-%m-%d"),
                'quantity': 1
            })

        # Ensure the session is saved after modification
        session.modified = True

        return jsonify(session['rented_movies'])

    except Exception as e:
        print("Error executing SQL query:", e)
        return jsonify({'error': 'Database query error'})









































# @app.route('/scan_movie', methods=['POST'])
# def scan_movie():
#     barcode = request.form.get('barcode')
#     print("Received barcode:", barcode)  # Debugging statement

#     try:
#         cursor.execute("SELECT Movie_ID, Title FROM Movies WHERE Movie_Barcode = ?", (barcode,))
#         movie = cursor.fetchone()
#         print("Fetched movie details:", movie)  # Debugging statement
#     except Exception as e:
#         print("Error executing SQL query:", e)
#         return jsonify({'error': 'Database query error'})

#     if movie:
#         rent_date = date.today()
#         return_date = rent_date + timedelta(weeks=1)
        
#         if 'rented_movies' not in session:
#             session['rented_movies'] = []

#         movie_found = False
#         for rented_movie in session['rented_movies']:
#             if rented_movie['movie_id'] == movie[0]:
#                 rented_movie['quantity'] += 1
#                 movie_found = True
#                 break

#         if not movie_found:
#             session['rented_movies'].append({
#                 'movie_id': movie[0],
#                 'movie_title': movie[1],
#                 'rent_date': rent_date.strftime("%Y-%m-%d"),
#                 'return_date': return_date.strftime("%Y-%m-%d"),
#                 'quantity': 1
#             })

#         return jsonify(session['rented_movies'])
#     else:
#         return jsonify({'error': 'Movie not found'})










## A table that records the movie details for a rental transaction.
# @app.route('/get_movie_details', methods=['POST'])
# def get_movie_details():
#     barcode = request.form.get('barcode')
#     print(f"Received barcode: {barcode}")

#     # Fetch movie details from the database
#     cursor.execute("SELECT Movie_ID, Title, Movie_Barcode FROM Movies WHERE Movie_Barcode = ?", (barcode,))
#     movie = cursor.fetchone()
    
#     if movie:
#         movie_details = {
#             "Movie_ID": movie.Movie_ID,
#             "Title": movie.Title,
#             "Barcode": movie.Movie_Barcode
#         }
#         return jsonify(movie_details)
#     else:
#         return jsonify({"error": "Movie not found"}), 404

# @app.route('/rental_checkout', methods=['POST'])
# def rental_checkout():
#     data = request.json
#     customer_id = data.get('customer_id')
#     customer_name = data.get('customer_name')
#     rent_date_str = data.get('rent_date')

#     rent_date = datetime.strptime(rent_date_str, '%m/%d/%Y')
#     return_date = rent_date + timedelta(days=7)

#     # Assuming you have a Rentals table in your database
#     cursor.execute("INSERT INTO Rentals (Customer_ID, Customer_Name, Rental_Date, Return_Date) VALUES (?, ?, ?, ?)", 
#                    (customer_id, customer_name, rent_date, return_date))
    
#     conn.commit()

#     return jsonify({"success": True})




# @app.route('/get_movie_details', methods=['POST'])
# def get_movie_details():
#     # Get the scanned barcode from the POST request
#     movie_barcode = request.form.get('movie_barcode')

#     # Fetch the movie details based on the barcode
#     cursor.execute("SELECT Movie_ID, Title, Movie_Barcode FROM Movies WHERE Barcode = ?", (movie_barcode,))
#     movie = cursor.fetchone()  # Fetch one record

#     if movie:
#         # Create a dictionary to send as a JSON response
#         movie_details = {
#             "Movie_ID": movie["Movie_ID"],
#             "Title": movie["Title"],
#             "Barcode": movie_barcode,
#         }
#         return jsonify(movie_details)  # Return as JSON
#     else:
#         return jsonify({"error": "Movie not found"}), 404  # Return an error if no movie found


# @app.route('/borrow_multiple_dvds', methods=['POST'])
# def borrow_multiple_dvds():
#     customer_id = request.form.get('customer_id')
#     borrow_date = datetime.now().date()
#     due_date = borrow_date + timedelta(days=7)  # Example: 7-day borrowing period

#     # A list of selected Movie_IDs
#     movie_barcode = request.form.get('movie_barcode')


#     # Create a new borrowing record
#     cursor.execute(
#         "INSERT INTO Borrowings (Customer_ID, Borrowing_Date, Due_Date) VALUES (?, ?, ?)",
#         (customer_id, borrow_date, due_date)
#     )
#     borrowing_id = cursor.lastrowid  # Get the generated Borrowing_ID

#     # Insert each Movie_ID into the Borrowing_Details table
#     for movie_id in movie_ids:
#         cursor.execute(
#             "INSERT INTO Borrowing_Details (Borrowing_ID, Movie_ID, Movie_Title, Movie_Barcode) VALUES (?, ?, ?, ?)",
#             (borrowing_id, movie_id, movie_title, movie_barcode)
#         )
    
#     cursor.execute(
#         "UPDATE Inventory SET Inventory_Availability = Inventory_Availability -1 WHERE Movie_Barcode =?",(movie_barcode,))
    

#     conn.commit()

#     return redirect(url_for('some_page'))  # Redirect to a relevant page after borrowing


# Function to check if a barcode already exists in the database
def barcode_exists(movie_barcode):
    cursor.execute("SELECT COUNT(*) FROM Movies WHERE Movie_Barcode=?", (movie_barcode,))
    count = cursor.fetchone()[0]
    return count > 0

# Function to update the access database by increasing qty of existing movies or insert a brand new movie into the database
def insert_or_update_movie_details(movie_barcode, movie_name):
    if barcode_exists(movie_barcode):
        # If barcode already exists, update the quantity
        cursor.execute("UPDATE Movies SET Quantity = Quantity + 1 WHERE Movie_Barcode=?", (movie_barcode,))
        cursor.execute("UPDATE Inventory SET Inventory_Availability = Inventory_Availability + 1, Total_Quantity = Total_Quantity + 1 WHERE Movie_Barcode =?", (movie_barcode,))
    else:
        # Perform a search for the movie
        ia = imdb.IMDb()
        movies = ia.search_movie(movie_name)

        # Retrieve details of the first movie
        movie = movies[0]
        ia.update(movie)

        # # Extracting movie details

        # Storing all the required movie details into a list
        movie_details = [{"Title" : movie['title'], "Year" : movie['year'], "Rating" : float(movie['rating']),
                            "Runtime" : int(movie['runtimes'][0]), "Director" : str(movie['director'][0]), "Genre": movie['genre']}]

        # Getting all the movie details 
        for i in movie_details:

            title = i.get('Title', '')
            release_year = i.get('Year', '')
            director = i.get('Director', '')
            rating = i.get('Rating', '')
            duration = i.get('Runtime', '')
            quantity = 1 
            Inventory_Quantity = 1 
            Availability_Status = "Available"

        # Insert movie details into the database
        cursor.execute("INSERT INTO Movies (Title, Release_Year, Director, Rating, Duration, Quantity, Movie_Barcode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (title, release_year, director, rating, duration, quantity, movie_barcode))
        conn.commit()
        print(f"Successfully inserted Movie with barcode: {movie_barcode}")

        # Extracting the Movie ID of the movie that is just being inserted
        cursor.execute("SELECT Movie_ID FROM Movies WHERE Movie_Barcode=?", (movie_barcode,))
        Movie_ID = cursor.fetchone()[0]

        # Insert Inventory details into the Inventory Table
        cursor.execute("INSERT INTO Inventory (Movie_ID, Movie_Title, Movie_Barcode, Inventory_Availability, Total_Quantity, Availability_Status) VALUES (?, ?, ?, ?, ?, ?)",
                       (Movie_ID, title, movie_barcode, Inventory_Quantity, quantity, Availability_Status))
        

    # Commit the transaction after database operations
    conn.commit()
    print(f"Successfully inserted Movie into Inventory with barcode: {movie_barcode}")


# Function to autogenerate a random password
import random
import string

def generate_password(min_length=8, max_length=15):
    # Define the character sets
    letters = string.ascii_letters  # A mix of uppercase and lowercase letters
    digits = string.digits  # Numbers from 0 to 9
    special_characters = "!@#$%^&*()_+[]{}|;:,.<>?~"  # Common special characters
    
    # Ensure the minimum requirements
    password = [
        random.choice(letters),
        random.choice(digits),
        random.choice(special_characters),
    ]
    
    # Fill the rest of the password length with a random mix of letters, digits, and special characters
    all_characters = letters + digits + special_characters
    password_length = random.randint(min_length, max_length)
    while len(password) < password_length:
        password.append(random.choice(all_characters))
    
    # Shuffle the password to avoid predictable patterns
    random.shuffle(password)
    
    # Join the list of characters into a string and return
    return "".join(password)



@app.route('/logout', methods=['POST'])
def logout():
    # Clear the session data
    session.clear()
    # Render the logout confirmation page
    return render_template('logout.html')

if __name__ == '__main__':
    app.run(debug=True)


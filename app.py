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



@app.before_request
def clear_session_on_load():
    if 'rented_movies' in session:
        session.pop('rented_movies', None)
        session.modified = True

        
# ROUTES 
# Routes for Login Purposes 
# The ROOT URL (need this to initiate the whole website) represented by ('/')
@app.route('/')
def index():
    error_message = request.args.get('error_message', '')
    return render_template('login.html', error_message=error_message)
    
## DONT DELETE THIS CODE TILL IT IS RESOLVED 
# # Retrieving Username and Password Inputs and Checking with the Database before moving to the next page.
# @app.route('/login', methods=['POST'])
# def login():
#     username = request.form.get('username')
#     password = request.form.get('password')
    
#     # Check if the provided username and password match in the Access database
#     cursor.execute("SELECT * FROM Staff WHERE Staff_Username = ? AND Staff_Password = ?",username, password)
#     user = cursor.fetchone()

#     if user:
#     # Successful login, redirect to a new page or perform additional actions
#         # The Name of the user is located at the second column of the Users table (index 1)
#         session['user_name'] = user[1]
#         return redirect(url_for('dashboard'))
#     else:
#         # Invalid credentials, redirect back to the login page with an error message
#         error_message = 'Invalid Username and/or Password!'
#         return redirect(url_for('index', error_message=error_message))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Check if the provided username and password match in the Access database
    cursor.execute("SELECT Staff_ID, Staff_FirstName FROM Staff WHERE Staff_Username = ? AND Staff_Password = ?", (username, password))
    staff = cursor.fetchone()

    if staff:
        # Successful login, store staff ID and redirect to dashboard
        session['staff_id'] = staff[0]  # Access tuple elements by index
        session['staff_name'] = staff[1]  # Access tuple elements by index
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
    user_name = session.get('staff_name')

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
    # Clear the session data
    session.pop('rented_movies', None)
    session.modified = True

    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        print("Received phone number:", phone_number)  # Debugging statement

        # Fetch customer details by phone number
        cursor.execute("SELECT Customer_ID, Customer_FirstName, Customer_LastName FROM Customers WHERE Customer_PhoneNumber = ?", (phone_number,))
        customer = cursor.fetchone()
        print("Fetched customer details:", customer)  # Debugging statement
        
        if customer:
            # Store customer details in session for further use
            session['customer_id'] = customer[0]  # Access tuple elements by index
            session['customer_name'] = f"{customer[1]} {customer[2]}"

            # Get the current date
            rent_date = date.today().strftime("%Y-%m-%d")

            # Render the page with customer details
            return render_template('get_customer_details.html', 
                                   customer_id=session['customer_id'], 
                                   customer_name=session['customer_name'],
                                   rent_date=rent_date,
                                   staff_id=session.get('staff_id'))  # Pass staff ID
    
        else:
            # If customer not found, display a message or handle the error
            return render_template('get_customer_details.html', error="Customer not found")
    
    # For GET request, just render the template without any data
    return render_template('get_customer_details.html')





@app.route('/scan_movie', methods=['POST'])
def scan_movie():
    barcode = request.form.get('barcode')
    session['barcode'] = barcode
    print("Received barcode:", barcode)  # Debugging statement

    try:
        # Fetch movie details
        cursor.execute("SELECT Movie_ID, Title FROM Movies WHERE Movie_Barcode = ?", (barcode,))
        movie = cursor.fetchone()
        print("Fetched movie details:", movie)  # Debugging statement

        if not movie:
            return jsonify({'error': 'Movie not found'})

        movie_id = movie[0]  # Access tuple elements by index
        print("Movie ID:", movie_id)
        movie_title = movie[1]
        print("Movie Title:", movie_title)

        # Check inventory availability
        cursor.execute("SELECT Inventory_Availability FROM Inventory WHERE Movie_ID = ?", (movie_id,))
        inventory = cursor.fetchone()
        print("Fetched inventory details:", inventory)  # Debugging statement

        if not inventory or inventory[0] <= 0:
            return jsonify({'error': 'Movie is fully RENTED OUT'})

        # Update inventory availability
        new_availability = inventory[0] - 1
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
                'quantity': 1,
                'barcode': barcode
            })

        # Ensure the session is saved after modification
        session.modified = True

        return jsonify(session['rented_movies'])

    except Exception as e:
        print("Error executing SQL query:", e)
        return jsonify({'error': 'Database query error'})




@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        customer_id = session.get('customer_id')
        customer_name = session.get('customer_name')
        staff_id = session.get('staff_id')
        rented_movies = request.json.get('movies', [])

        if not customer_id or not customer_name or not staff_id or not rented_movies:
            return jsonify({'error': 'Missing customer or rental information'})

        rental_date = date.today()
        return_date = rental_date + timedelta(weeks=1)

        # Set default rental status to 'Due'
        rental_status = 'Due'

        # Insert rental record into the Rentals table
        cursor.execute("""
            INSERT INTO Rentals (Customer_ID, Customer_Name, Rental_Date, Return_Date, Staff_ID, Status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (customer_id, customer_name, rental_date, return_date, staff_id, rental_status))
        conn.commit()

        # Retrieve the last inserted Rental_ID
        cursor.execute("SELECT MAX(Rental_ID) FROM Rentals")
        rental_id = cursor.fetchone()[0]

        # Debugging: Print rented movies
        print("Rented movies data:", rented_movies)
        
        # Insert rental details and update inventory
        for movie in rented_movies:
            if 'movie_id' not in movie or 'movie_title' not in movie or 'barcode' not in movie or 'quantity' not in movie:
                return jsonify({'error': 'Invalid movie data format'})
            
            # Extract the inventory_Id based on the movie barcode
            cursor.execute("SELECT Inventory_ID FROM Inventory WHERE Movie_Barcode = ?", (movie['barcode'],))
            inventory_id = cursor.fetchone()

            # Check if the Inventory_ID was found
            if not inventory_id:
                return jsonify({'error': f"Inventory not found for movie with barcode {movie['barcode']}"})

            # Set the default status for each movie as 'Due'
            movie_status = 'Due'

            # Insert the details into the Rental_Details table
            cursor.execute("""
                INSERT INTO Rental_Details (Rental_ID, Movie_ID, Movie_Title, Movie_Barcode, Quantity, Inventory_ID, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (rental_id, movie['movie_id'], movie['movie_title'], movie['barcode'], movie['quantity'], inventory_id[0], movie_status))

        conn.commit()

        # Clear session rented movies
        session.pop('rented_movies', None)
        session.modified = True

        return jsonify({'success': 'Rental Transaction Successful!'})

    except Exception as e:
        print("Error during checkout:", e)
        return jsonify({'error': 'Checkout failed due to a database error'})



# Route for fetching rental details based on customer phone number
@app.route('/get_rental_details', methods=['POST', 'GET'])
def get_rental_details():
    if request.method == 'POST':
        try:
            phone_number = request.form.get('phone_number')
            print("Phone Number Entered:", phone_number)  # DEBUG: Check phone number input

            # Fetch customer details based on phone number
            cursor.execute("SELECT Customer_ID, Customer_FirstName, Customer_LastName FROM Customers WHERE Phone_Number = ?", (phone_number,))
            customer = cursor.fetchone()
            print("Customer Fetched:", customer)  # DEBUG: Check if customer is fetched

            if not customer:
                return render_template('rental_details.html', error='Customer not found')

            customer_id = customer[0]
            customer_name = customer[1]

            # Fetch all active rentals for this customer
            cursor.execute("""
                SELECT Rentals.Rental_ID, Rental_Details.Movie_Title, Rental_Details.Movie_Barcode, Rental_Details.Quantity, 
                       Rental_Details.Status, Rentals.Return_Date
                FROM Rentals
                INNER JOIN Rental_Details ON Rentals.Rental_ID = Rental_Details.Rental_ID
                WHERE Rentals.Customer_ID = ? AND Rental_Details.Status != 'Completed'
            """, (customer_id,))
            rentals = cursor.fetchall()
            print("Rentals Fetched:", rentals)  # DEBUG: Check if rentals are fetched

            if not rentals:
                return render_template('rental_details.html', error='No active rentals found for this customer')

            rental_data = [
                {
                    'rental_id': rental[0],
                    'movie_title': rental[1],
                    'barcode': rental[2],
                    'quantity': rental[3],
                    'status': rental[4],
                    'return_date': rental[5]
                }
                for rental in rentals
            ]

            # Render the HTML template and pass the customer and rental data to it
            return render_template('returning_movie.html', customer_name=customer_name, phone_number=phone_number, rentals=rental_data)

        except Exception as e:
            print("Error fetching rental details:", e)  # DEBUG: Error log
            return render_template('returning_movie.html', error='Failed to retrieve rental details')

    return render_template('returning_movie.html')  # Render the template initially without any data



# Function that processes the returning of the DVDs (Updating the Status)
@app.route('/process_return', methods=['POST'])
def process_return():
    try:
        rental_data = request.json.get('rentals', [])

        for rental in rental_data:
            rental_id = rental['rental_id']
            barcode = rental['barcode']

            # Mark the DVD as returned (status = Completed)
            cursor.execute("""
                UPDATE Rental_Details
                SET Status = 'Completed'
                WHERE Rental_ID = ? AND Movie_Barcode = ?
            """, (rental_id, barcode))

            # Check if all movies in this rental are completed
            cursor.execute("""
                SELECT COUNT(*) FROM Rental_Details
                WHERE Rental_ID = ? AND Status != 'Completed'
            """, (rental_id,))
            remaining_movies = cursor.fetchone()[0]

            # Update the Rental Status
            if remaining_movies == 0:
                cursor.execute("UPDATE Rentals SET Rental_Status = 'Completed' WHERE Rental_ID = ?", (rental_id,))
            else:
                cursor.execute("""
                    UPDATE Rentals SET Rental_Status = CASE 
                        WHEN Return_Date < ? THEN 'Overdue' ELSE 'Due' END
                    WHERE Rental_ID = ?
                """, (date.today(), rental_id))

        conn.commit()

        return jsonify({'success': 'Return process completed successfully'})

    except Exception as e:
        conn.rollback()  # Rollback if error occurs
        print("Error during return process:", e)
        return jsonify({'error': 'Failed to process return'})



























# Function to update the rental Status in the Rental Databases
def update_rental_status(rental_id):
    try:
        # Fetch all rental details for the given Rental_ID
        cursor.execute("""
            SELECT Movie_ID, Return_Date, Status 
            FROM Rental_Details 
            WHERE Rental_ID = ?
        """, (rental_id,))
        rental_details = cursor.fetchall()

        today = date.today()
        all_returned = True
        any_overdue = False

        # Check and update the status for each movie
        for movie in rental_details:
            movie_id = movie[0]
            return_date = movie[1]
            status = movie[2]

            if status != 'Completed':
                # Check if the movie is overdue or due
                if return_date < today:
                    new_status = 'Overdue'
                    any_overdue = True
                else:
                    new_status = 'Due'
                    all_returned = False

                # Update the status if it has changed
                if new_status != status:
                    cursor.execute("""
                        UPDATE Rental_Details 
                        SET Status = ? 
                        WHERE Rental_ID = ? AND Movie_ID = ?
                    """, (new_status, rental_id, movie_id))
                    conn.commit()

        # Set the overall rental status based on the movies' statuses
        if all_returned:
            rental_status = 'Completed'
        elif any_overdue:
            rental_status = 'Overdue'
        else:
            rental_status = 'Due'

        # Update the rental status in the Rentals table
        cursor.execute("""
            UPDATE Rentals 
            SET Rental_Status = ? 
            WHERE Rental_ID = ?
        """, (rental_status, rental_id))
        conn.commit()

    except Exception as e:
        print("Error updating rental status:", e)

# Function to find the barcode for a given movie_id 
def get_barcode_for_title(movies, movie_id):
    for movie in movies:
        if movie['movie_id'] == movie_id:
            return movie['barcode']
    return None


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


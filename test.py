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
    






<!-- add_movie.html -->

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add New Movie</title>
</head>
<body>
    <h1>Add New Movie</h1>
    <form action="/add_movie" method="POST">
        <label for="movie_name">Movie Name:</label>
        <input type="text" id="movie_name" name="movie_name" required><br>
        <label for="movie_barcode">Movie Barcode:</label>
        <input type="text" id="movie_barcode" name="movie_barcode" required><br>
        <button type="submit">Search Movie Details</button>
    </form>
    
    {% if movie_details %}
    <h2>Movie Details</h2>
    <ul>
        <li><strong>Title:</strong> {{ movie_details.Title }}</li>
        <li><strong>Year:</strong> {{ movie_details.Year }}</li>
        <li><strong>Director:</strong> {{ movie_details.Director }}</li>
        <li><strong>Rating:</strong> {{ movie_details.Rating }}</li>
        <li><strong>Runtime:</strong> {{ movie_details.Runtime }}</li>
    </ul>
    <form action="/update_movie" method="POST">
        <input type="hidden" name="title" value="{{ movie_details.Title }}">
        <input type="hidden" name="year" value="{{ movie_details.Year }}">
        <input type="hidden" name="director" value="{{ movie_details.Director }}">
        <input type="hidden" name="rating" value="{{ movie_details.Rating }}">
        <input type="hidden" name="runtime" value="{{ movie_details.Runtime }}">
        <input type="hidden" name="barcode" value="{{ movie_barcode }}">
        <button type="submit">Add Movie</button>
    </form>
    {% endif %}
</body>
</html>


    
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

        # Insert rental record into the Rentals table
        cursor.execute("""
            INSERT INTO Rentals (Customer_ID, Customer_Name, Rental_Date, Return_Date, Staff_ID)
            VALUES (?, ?, ?, ?, ?)
        """, (customer_id, customer_name, rental_date, return_date, staff_id))
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

            # Insert the details into the Rental_Details table
            cursor.execute("""
                INSERT INTO Rental_Details (Rental_ID, Movie_ID, Movie_Title, Movie_Barcode, Quantity, Inventory_ID)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rental_id, movie['movie_id'], movie['movie_title'], movie['barcode'], movie['quantity'], inventory_id[0]))

        conn.commit()

        # Clear session rented movies
        session.pop('rented_movies', None)
        session.modified = True

        return jsonify({'success': 'Rental Transaction Successful!'})

    except Exception as e:
        print("Error during checkout:", e)
        return jsonify({'error': 'Checkout failed due to a database error'})

# Handles movie barcode scanning and populate the table with movie rental details
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

        return jsonify(session['rented_movies'])

    except Exception as e:
        print("Error executing SQL query:", e)
        return jsonify({'error': 'Database query error'})

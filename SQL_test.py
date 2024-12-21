from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import date, timedelta
import imdb
import pyodbc
import random
import string

conn_str = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ= C:\Users\Systems\Documents\DVD_Inventory_Website\Movie_Database.accdb;'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Fetch all active rentals for this customer
cursor.execute("""
    SELECT Rentals.Rental_ID, Rental_Details.Movie_Title, Rental_Details.Movie_Barcode, Rental_Details.Quantity, 
            Rental_Details.Status, Rentals.Return_Date
    FROM Rentals
    INNER JOIN Rental_Details ON Rentals.Rental_ID = Rental_Details.Rental_ID
    WHERE Rentals.Customer_ID = 3 AND Rental_Details.Status <> 'Completed'
""")
rentals = cursor.fetchall()
print("Rentals Fetched:", rentals)  # DEBUG: Check if rentals are fetched


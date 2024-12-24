# -*- coding: utf-8 -*-
"""Amazon_discount.ipynb
Original file is located at
    https://colab.research.google.com/drive/1fPm9hQ9-0-VrBTZKmArtbIwf1rAD2wjR
"""


from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



# Initialize database connection
def init_db():
    conn = sqlite3.connect("discounts.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS discounts (
        id INTEGER PRIMARY KEY,
        name TEXT,
        price REAL,
        discount REAL,
        last_updated TEXT
    )
    """)
    conn.commit()
    return conn

# Save data to the database
def save_to_db(conn, data):
    cursor = conn.cursor()
    for record in data:
        cursor.execute("""
        INSERT OR REPLACE INTO discounts (id, name, price, discount, last_updated)
        VALUES (?, ?, ?, ?, ?)
        """, (record["id"], record["name"], record["price"], record["discount"], record["last_updated"]))
    conn.commit()

# Fetch Amazon data (mocked for demonstration)
def fetch_amazon_data(product_ids):
    data = []
    for product_id in product_ids:
        # Mock API or scraping call (replace with actual logic)
        response = {
            "id": product_id,
            "name": f"Product {product_id}",
            "price": 100 - product_id,  # Mocked discount logic
            "discount": product_id % 20,
            "last_updated": datetime.now().isoformat()
        }
        data.append(response)
        time.sleep(0.1)  # Simulate delay
    return data

# Function to convert data to JSON Lines format
def convert_to_jsonl(data):
    jsonl_data = "\n".join([json.dumps(record) for record in data])
    return jsonl_data

# Fetch and process data in parallel
def parallel_fetch_and_process(product_ids):
    with ThreadPoolExecutor() as executor:
        chunks = [product_ids[i:i + 10] for i in range(0, len(product_ids), 10)]
        results = executor.map(fetch_amazon_data, chunks)
        processed_data = [item for sublist in results for item in sublist]
    return processed_data

# Notify user of significant discounts
def notify_user(email, message):
    sender_email = "your_email@example.com"
    sender_password = "your_password"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = "Significant Discounts Alert"

    msg.attach(MIMEText(message, "plain"))

    try:
        with smtplib.SMTP("smtp.example.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")

# Load environment variables from .env
load_dotenv()

# Access the variables
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
smtp_server = os.getenv("SMTP_SERVER", "smtp.example.com")
smtp_port = int(os.getenv("SMTP_PORT", "587"))


# Advanced query to find significant discounts
def find_significant_discounts(conn, threshold):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM discounts WHERE discount >= ?
    """, (threshold,))
    return cursor.fetchall()

# Enhanced email system
def enhanced_notify_user(email, significant_discounts):
    sender_email = "your_email@example.com"
    sender_password = "your_password"
    smtp_server = "smtp.example.com"
    smtp_port = 587

    # Construct the email content
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = "Amazon Discount Tracker: Significant Discounts"

    body = "<h2>Significant Discounts Detected</h2><ul>"
    for discount in significant_discounts:
        body += f"<li>Product ID: {discount[0]}, Name: {discount[1]}, Price: {discount[2]}, Discount: {discount[3]}%</li>"
    body += "</ul><p>Thank you for using Amazon Discount Tracker!</p>"

    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# Scheduler for periodic updates
def schedule_updates(conn, product_ids, email):
    def update_job():
        st.write("Running scheduled update...")
        fetched_data = parallel_fetch_and_process(product_ids)
        save_to_db(conn, fetched_data)
        significant_discounts = find_significant_discounts(conn, 15)
        if significant_discounts:
            enhanced_notify_user(email, significant_discounts)
        st.write("Database updated with latest discounts.")

    scheduler = BackgroundScheduler()
    scheduler.add_job(update_job, 'interval', minutes=10)  # Run every 10 minutes
    scheduler.start()

# Streamlit App
st.title("Amazon Discount Tracker")

# Initialize database
conn = init_db()

# Input for product IDs
product_ids_input = st.text_input("Enter Product IDs (comma-separated):", "1,2,3,4,5")

# Input for notification email
email_input = st.text_input("Enter your email for notifications:")

if product_ids_input:
    product_ids = [int(id.strip()) for id in product_ids_input.split(",")]

    st.write("Fetching real-time data...")

    # Fetch data
    fetched_data = parallel_fetch_and_process(product_ids)

    # Save to database
    save_to_db(conn, fetched_data)

    # Convert to JSON Lines
    jsonl_data = convert_to_jsonl(fetched_data)

    # Display data
st.subheader("Fetched Discounts")
# Instead of loading the whole jsonl_data string
# Iterate and load each line as a separate JSON object
for i, line in enumerate(jsonl_data.splitlines()):
    st.json(json.loads(line))

    # Allow download of JSONL data with a unique key for each button
    st.download_button(
        label=f"Download JSONL {i}",
        data=jsonl_data,
        file_name=f"amazon_discounts_{i}.jsonl",  # Unique file name for each download
        mime="application/jsonl",
        key=f"download_button_{i}"  # Unique key for each download button
    )

    # Schedule periodic updates
    if st.button("Enable Real-Time Updates"):
        if email_input:
            schedule_updates(conn, product_ids, email_input)
            st.write("Real-time updates enabled. Data will refresh every 10 minutes and email notifications will be sent for significant discounts.")
        else:
            st.error("Please provide a valid email address for notifications.")

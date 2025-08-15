import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

import openai
import requests

from config import ORIGIN, DESTINATION, DATE_FROM, DATE_TO, NIGHTS_IN_DST_FROM, NIGHTS_IN_DST_TO, MAX_PRICE
from email_formatter import build_email_body

# Email recipient from environment
SEND_TO = os.getenv("EMAIL_RECEIVER")

def search_flights():
    """Query flight search API for results"""
    url = "https://api.tequila.kiwi.com/v2/search"
    headers = {"apikey": os.getenv("KIWI_API_KEY")}
    params = {
        "fly_from": ORIGIN,
        "fly_to": DESTINATION,
        "date_from": DATE_FROM,
        "date_to": DATE_TO,
        "nights_in_dst_from": NIGHTS_IN_DST_FROM,
        "nights_in_dst_to": NIGHTS_IN_DST_TO,
        "price_to": MAX_PRICE,
        "curr": "USD",
        "limit": 5,
        "sort": "price",
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json().get("data", [])


def send_email(subject: str, body: str):
    """Send email using SMTP"""
    msg = MIMEMultipart("alternative")
    msg["From"] = os.getenv("EMAIL_SENDER")
    msg["To"] = SEND_TO
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg)


def main():
    try:
        flights = search_flights()

        if not flights:
            print("No flights found.")
            return

        # Prepare email
        subject = f"Found {len(flights)} flight(s) from {ORIGIN} to {DESTINATION}"
        body = build_email_body(flights, ORIGIN, DESTINATION)

        # Send email
        send_email(subject, body)
        print("Email sent successfully!")

    except Exception as e:
        send_email("Flight Search Failed", f"Unexpected failure: {str(e)}")
        raise


if __name__ == "__main__":
    main()

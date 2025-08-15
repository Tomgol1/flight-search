import os
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from amadeus import Client, ResponseError
import openai
from config import ORIGIN, DESTINATION, DEPARTURE_DATE, RETURN_DATE, ALLOW_NEXT_DAY, MAX_RESULTS
from email_formatter import build_email_body

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("flight_search.log"),
        logging.StreamHandler()
    ]
)

# --- Load Environment Variables ---
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SEND_TO = os.getenv("EMAIL_RECEIVER")
if not SEND_TO:
    raise ValueError("EMAIL_RECEIVER environment variable not set")

# --- Setup Clients ---
amadeus = Client(client_id=AMADEUS_API_KEY, client_secret=AMADEUS_API_SECRET)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# --- Helper Functions ---
def search_flights(origin, destination, departure_date, return_date, max_results=5):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            returnDate=return_date,
            adults=1,
            max=max_results
        )
        flights = response.data
        logging.info(f"Found {len(flights)} flights for {departure_date} → {return_date}")
        return flights
    except ResponseError as e:
        logging.error(f"Amadeus API error: {e}")
        return []

def summarize_with_ai(flights):
    if not flights:
        return "No flights found."

    try:
        flight_descriptions = [
            f"{f['itineraries'][0]['segments'][0]['carrierCode']} "
            f"{f['itineraries'][0]['segments'][0]['departure']['iataCode']}->"
            f"{f['itineraries'][0]['segments'][-1]['arrival']['iataCode']}, "
            f"${f['price']['total']}"
            for f in flights
        ]

        prompt = "Summarize these flight options in a helpful way:\n" + "\n".join(flight_descriptions)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )

        summary = response.choices[0].message.content
        logging.info("AI summary generated successfully")
        return summary

    except openai.RateLimitError:
        logging.warning("OpenAI quota exceeded or rate limited, skipping AI summary.")
        return "AI summary unavailable due to OpenAI quota limits."
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return "AI summary failed."

def send_email(subject, html_body, recipient):
    try:
        msg = MIMEText(html_body, "html")
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = recipient

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, recipient, msg.as_string())

        logging.info(f"Email sent to {recipient}")
    except Exception as e:
        logging.error(f"Email sending failed: {e}")

def build_search_link(origin, destination, departure_date, return_date):
    return f"https://www.kayak.com/flights/{origin}-{destination}/{departure_date}/{return_date}?sort=bestflight_a"

# --- Main Job ---
def run_job():
    try:
        departure_dates = [DEPARTURE_DATE]
        return_dates = [RETURN_DATE]
        if ALLOW_NEXT_DAY:
            dep_plus = (datetime.strptime(DEPARTURE_DATE, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            ret_plus = (datetime.strptime(RETURN_DATE, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            departure_dates.append(dep_plus)
            return_dates.append(ret_plus)

        all_flights = []
        for dep in departure_dates:
            for ret in return_dates:
                flights = search_flights(ORIGIN, DESTINATION, dep, ret, MAX_RESULTS)
                all_flights.extend(flights)

        if not all_flights:
            send_email("Flight Search Results", "<p>No flights found.</p>", SEND_TO)
            return

        summary = summarize_with_ai(all_flights)
        html_body = build_email_body(all_flights, departure_dates, return_dates, summary)
        send_email("Flight Search Results", html_body, SEND_TO)

    except Exception as e:
        logging.critical(f"Unexpected failure: {e}")
        send_email("Flight Search FAILED", f"<p>Error: {e}</p>", SEND_TO)

if __name__ == "__main__":
    run_job()

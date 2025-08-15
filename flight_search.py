import os
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from amadeus import Client, ResponseError
import openai

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("flight_search.log"),
        logging.StreamHandler()
    ]
)

# --- Load Environment Variables (GitHub Secrets) ---
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SEND_TO = os.getenv("EMAIL_RECEIVER")

# --- Configurable Parameters ---
ORIGIN = "NYC"             # city or airport code
DESTINATION = "LON"        # city or airport code
DEPARTURE_DATE = "2025-09-01"
RETURN_DATE = "2025-09-10"
ALLOW_NEXT_DAY = True
MAX_RESULTS = 10

# --- Setup Amadeus Client ---
amadeus = Client(client_id=AMADEUS_API_KEY, client_secret=AMADEUS_API_SECRET)

# --- Setup OpenAI Client (1.0+ interface) ---
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

def send_email(subject, body, recipient):
    try:
        msg = MIMEText(body)
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
        # Build list of departure/return dates
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
            send_email("Flight Search Results", "No flights found.", SEND_TO)
            return

        # Generate AI summary
        summary = summarize_with_ai(all_flights)

        # Build email body
        body = "Flight Search Results:\n\n"
        for f in all_flights:
            price = f["price"]["total"]
            dep = f["itineraries"][0]["segments"][0]["departure"]["iataCode"]
            arr = f["itineraries"][0]["segments"][-1]["arrival"]["iataCode"]
            carrier = f["itineraries"][0]["segments"][0]["carrierCode"]
            body += f"{carrier} {dep}->{arr}, ${price}\n"

        body += "\nFlight Search Links:\n"
        for dep in departure_dates:
            for ret in return_dates:
                link = build_search_link(ORIGIN, DESTINATION, dep, ret)
                body += f"{dep} → {ret}: {link}\n"

        body += "\n\n---\nAI Summary:\n" + summary

        # Send email
        send_email("Flight Search Results", body, SEND_TO)

    except Exception as e:
        logging.critical(f"Unexpected failure: {e}")
        send_email("Flight Search FAILED", f"Error: {e}", SEND_TO)

if __name__ == "__main__":
    run_job()

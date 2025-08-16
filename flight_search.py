import os
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from amadeus import Client, ResponseError
import anthropic
from config import ORIGIN, DESTINATION, DEPARTURE_DATE, RETURN_DATE, ALLOW_NEXT_DAY, MAX_RESULTS
from email_formatter import build_email_body

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("flight_search.log"),
        logging.StreamHandler()
    ]
)

# --- Environment Variables ---
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SEND_TO = os.getenv("EMAIL_RECEIVER")
if not SEND_TO:
    raise ValueError("EMAIL_RECEIVER environment variable not set")

# --- Clients ---
amadeus = Client(client_id=AMADEUS_API_KEY, client_secret=AMADEUS_API_SECRET)
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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

def summarize_with_claude(flights):
    if not flights:
        return "No flights found."

    try:
        # Create detailed flight information for Claude
        flight_details = []
        for i, flight in enumerate(flights, 1):
            dep_seg = flight['itineraries'][0]['segments'][0]
            arr_seg = flight['itineraries'][0]['segments'][-1]
            
            # Extract flight details
            airline = dep_seg['carrierCode']
            departure_airport = dep_seg['departure']['iataCode']
            arrival_airport = arr_seg['arrival']['iataCode']
            departure_time = dep_seg['departure']['at']
            arrival_time = arr_seg['arrival']['at']
            duration = flight['itineraries'][0]['duration']
            price = flight['price']['total']
            currency = flight['price']['currency']
            stops = len(flight['itineraries'][0]['segments']) - 1
            
            flight_info = (
                f"Flight {i}: {airline} {departure_airport}→{arrival_airport}, "
                f"Departs: {departure_time}, Arrives: {arrival_time}, "
                f"Duration: {duration}, Stops: {stops}, "
                f"Price: {price} {currency}"
            )
            flight_details.append(flight_info)

        # Create prompt for Claude
        prompt = f"""Please analyze these flight options and provide a helpful summary for a traveler:

{chr(10).join(flight_details)}

Please provide:
1. The cheapest option
2. The fastest/shortest duration option  
3. The best overall value (considering price, duration, and convenience)
4. Any notable patterns or recommendations

Keep the summary concise and actionable for someone deciding which flight to book."""

        # Call Claude API
        response = claude_client.messages.create(
            model="claude-3-haiku-20240307",  # Free tier friendly model
            max_tokens=200,  # Keep it concise to save tokens
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        summary = response.content[0].text
        logging.info("Claude AI summary generated successfully")
        return summary

    except anthropic.RateLimitError:
        logging.warning("Claude API rate limit exceeded, skipping AI summary.")
        return "AI summary unavailable due to Claude API rate limits."
    except anthropic.APIError as e:
        logging.error(f"Claude API error: {e}")
        return "AI summary failed due to API error."
    except Exception as e:
        logging.error(f"Unexpected error in Claude summary: {e}")
        return "AI summary failed due to unexpected error."

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

        summary = summarize_with_claude(all_flights)
        html_body = build_email_body(all_flights, departure_dates, return_dates, summary, ORIGIN, DESTINATION)
        send_email("Flight Search Results", html_body, SEND_TO)

    except Exception as e:
        logging.critical(f"Unexpected failure: {e}")
        send_email("Flight Search FAILED", f"<p>Error: {e}</p>", SEND_TO)

if __name__ == "__main__":
    run_job()

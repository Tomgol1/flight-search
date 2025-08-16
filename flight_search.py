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

# Validate required environment variables
if not SEND_TO:
    raise ValueError("EMAIL_RECEIVER environment variable not set")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
logging.info(f"ANTHROPIC_API_KEY present: {bool(ANTHROPIC_API_KEY)}")
logging.info(f"ANTHROPIC_API_KEY starts with sk-ant-: {ANTHROPIC_API_KEY.startswith('sk-ant-') if ANTHROPIC_API_KEY else False}")

# --- Clients ---
amadeus = Client(client_id=AMADEUS_API_KEY, client_secret=AMADEUS_API_SECRET)

# Initialize Claude client with explicit error handling
try:
    claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    logging.info("Claude client initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Claude client: {e}")
    claude_client = None

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

    # First try simple local analysis
    try:
        summary = create_local_summary(flights)
        logging.info("Using local flight summary (no AI)")
        return summary
    except Exception as e:
        logging.error(f"Local summary failed: {e}")
        return "Flight analysis temporarily unavailable."

def create_local_summary(flights):
    """Create a summary without AI - analyze flights locally"""
    if not flights:
        return "No flights found."
    
    # Extract flight data for analysis
    flight_analysis = []
    for i, flight in enumerate(flights, 1):
        dep_seg = flight['itineraries'][0]['segments'][0]
        arr_seg = flight['itineraries'][0]['segments'][-1]
        
        # Parse duration (format like "PT4H30M")
        duration_str = flight['itineraries'][0]['duration']
        duration_minutes = parse_duration_to_minutes(duration_str)
        
        price = float(flight['price']['total'])
        currency = flight['price']['currency']
        stops = len(flight['itineraries'][0]['segments']) - 1
        airline = dep_seg['carrierCode']
        
        flight_analysis.append({
            'index': i,
            'price': price,
            'currency': currency,
            'duration_minutes': duration_minutes,
            'duration_str': duration_str,
            'stops': stops,
            'airline': airline,
            'departure_airport': dep_seg['departure']['iataCode'],
            'arrival_airport': arr_seg['arrival']['iataCode']
        })
    
    # Find cheapest, fastest, and best value
    cheapest = min(flight_analysis, key=lambda x: x['price'])
    fastest = min(flight_analysis, key=lambda x: x['duration_minutes'])
    
    # Calculate "value score" (lower is better: price per hour)
    for flight in flight_analysis:
        flight['value_score'] = flight['price'] / (flight['duration_minutes'] / 60)
    
    best_value = min(flight_analysis, key=lambda x: x['value_score'])
    
    # Build summary
    summary_parts = []
    
    summary_parts.append(f"📊 <strong>Flight Analysis Summary:</strong><br>")
    summary_parts.append(f"Found {len(flights)} flight options.<br><br>")
    
    summary_parts.append(f"💰 <strong>Cheapest:</strong> Option {cheapest['index']} - {cheapest['price']} {cheapest['currency']} ({cheapest['airline']}, {cheapest['duration_str']}, {cheapest['stops']} stops)<br><br>")
    
    summary_parts.append(f"⚡ <strong>Fastest:</strong> Option {fastest['index']} - {fastest['duration_str']} ({fastest['airline']}, {fastest['price']} {fastest['currency']}, {fastest['stops']} stops)<br><br>")
    
    if best_value['index'] != cheapest['index'] and best_value['index'] != fastest['index']:
        summary_parts.append(f"⭐ <strong>Best Value:</strong> Option {best_value['index']} - Good balance of price and speed ({best_value['airline']}, {best_value['price']} {best_value['currency']}, {best_value['duration_str']})<br><br>")
    
    # Add some basic insights
    avg_price = sum(f['price'] for f in flight_analysis) / len(flight_analysis)
    direct_flights = [f for f in flight_analysis if f['stops'] == 0]
    
    if direct_flights:
        summary_parts.append(f"✈️ {len(direct_flights)} direct flight(s) available<br>")
    
    summary_parts.append(f"📈 Average price: {avg_price:.0f} {flight_analysis[0]['currency']}")
    
    return "".join(summary_parts)

def parse_duration_to_minutes(duration_str):
    """Parse ISO 8601 duration (PT4H30M) to minutes"""
    import re
    # Remove PT prefix
    duration_str = duration_str.replace('PT', '')
    
    hours = 0
    minutes = 0
    
    # Extract hours
    hour_match = re.search(r'(\d+)H', duration_str)
    if hour_match:
        hours = int(hour_match.group(1))
    
    # Extract minutes  
    min_match = re.search(r'(\d+)M', duration_str)
    if min_match:
        minutes = int(min_match.group(1))
    
    return hours * 60 + minutes

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

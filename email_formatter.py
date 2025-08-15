from datetime import datetime

def _format_datetime(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%a, %d %b %Y %H:%M")
    except Exception:
        return dt_str

def build_email_body(flights, departure_dates, return_dates, ai_summary, origin, destination):
    """
    flights: list of flight dicts from Amadeus API
    departure_dates, return_dates: list of strings
    ai_summary: string
    origin, destination: str
    """
    if not flights:
        return "<p>No flights found.</p>"

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f4f6f7; padding:20px; color:#333;">
        <h2 style="text-align:center; color:#2c3e50;">✈️ Flight Search Results</h2>
        <p style="text-align:center;">From <b>{origin}</b> to <b>{destination}</b></p>
        <hr style="margin:20px 0; border:none; border-top:1px solid #ddd;">
        <div style="max-width:700px; margin:auto;">
            <h3 style="color:#34495e;">AI Summary</h3>
            <p>{ai_summary}</p>
    """

    for idx, flight in enumerate(flights, start=1):
        dep_seg = flight['itineraries'][0]['segments'][0]
        arr_seg = flight['itineraries'][0]['segments'][-1]
        dep_time = _format_datetime(dep_seg['departure']['at'])
        arr_time = _format_datetime(arr_seg['arrival']['at'])
        duration = flight.get('itineraries')[0].get('duration', "N/A")
        price = flight.get('price', {}).get('total', "N/A")
        stops = len(flight['itineraries'][0]['segments']) - 1

        html += f"""
        <div style="background:white; padding:15px; border-radius:10px; margin-bottom:15px;
                    box-shadow:0 2px 6px rgba(0,0,0,0.08);">
            <p style="font-weight:bold; font-size:16px;">Option {idx}</p>
            <p>Route: <b>{dep_seg['departure']['iataCode']}</b> → <b>{arr_seg['arrival']['iataCode']}</b></p>
            <p>Departure: {dep_time} | Arrival: {arr_time}</p>
            <p>Duration: {duration} | Stops: {stops}</p>
            <p style="font-weight:bold; color:#27ae60;">Price: {price}</p>
        </div>
        """

    html += "</div></body></html>"
    return html

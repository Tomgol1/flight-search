from datetime import datetime

def format_datetime(dt_str):
    """Convert datetime string to readable format (assumes ISO 8601)."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%a, %d %b %Y %H:%M")
    except Exception:
        return dt_str  # fallback

def build_email_body(flights, origin, destination):
    if not flights:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; color: #333;">
            <h2 style="color:#444;">No Flights Found</h2>
            <p>There are no available flights from <b>{origin}</b> to <b>{destination}</b> at the moment.</p>
        </body>
        </html>
        """

    rows = ""
    for flight in flights:
        airline = flight.get("airline", "Unknown Airline")
        price = flight.get("price", "N/A")
        departure = format_datetime(flight.get("departure", ""))
        arrival = format_datetime(flight.get("arrival", ""))
        dep_airport = flight.get("origin", origin)
        arr_airport = flight.get("destination", destination)
        stops = flight.get("stops", [])
        duration = flight.get("duration", "N/A")

        stop_info = "Direct Flight"
        if stops:
            stop_info = "<br>".join(
                [f"Stop in {s.get('airport', '???')} ({s.get('duration', '')})" for s in stops]
            )

        rows += f"""
        <tr style="background-color: #fff;">
            <td style="padding: 15px; border-bottom: 1px solid #ddd;">
                <div style="font-size: 16px; font-weight: bold; color: #2c3e50;">{airline}</div>
                <div style="margin-top: 8px; font-size: 14px; color: #555;">
                    <b>{dep_airport}</b> → <b>{arr_airport}</b><br>
                    <span>Departure: {departure}</span><br>
                    <span>Arrival: {arrival}</span><br>
                    <span>Duration: {duration}</span><br>
                    <span>{stop_info}</span>
                </div>
            </td>
            <td style="padding: 15px; border-bottom: 1px solid #ddd; text-align: right; vertical-align: middle;">
                <div style="font-size: 18px; font-weight: bold; color: #27ae60;">{price}</div>
            </td>
        </tr>
        """

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f6f7; margin: 0; padding: 20px; color: #333;">
        <div style="max-width: 700px; margin: auto; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">
            <div style="background: linear-gradient(90deg, #4facfe, #00f2fe); padding: 20px; color: white; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">Flight Search Results</h1>
                <p style="margin: 5px 0 0 0; font-size: 14px;">{origin} → {destination}</p>
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                {rows}
            </table>
            <div style="padding: 15px; text-align: center; font-size: 12px; color: #888;">
                ✈️ Powered by Flight Search Bot
            </div>
        </div>
    </body>
    </html>
    """
    return html

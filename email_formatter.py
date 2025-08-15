from datetime import datetime

def build_email_body(flights, origin, destination):
    if not flights:
        return f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color:#444;">No Flights Found</h2>
            <p>We couldn’t find any flights from <b>{origin}</b> to <b>{destination}</b> at this time.</p>
          </body>
        </html>
        """

    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; background-color:#f9f9f9; padding:20px;">
        <h2 style="color:#2c3e50; margin-bottom:10px;">✈️ Flight Search Results</h2>
        <p style="margin-top:0;">From <b>{origin}</b> to <b>{destination}</b></p>
        <hr style="margin:20px 0; border:none; border-top:1px solid #ddd;">
    """

    for flight in flights:
        dep_time = _format_datetime(flight["departure_time"])
        arr_time = _format_datetime(flight["arrival_time"])
        stops = flight.get("stops", [])

        body += f"""
        <div style="background:white; padding:15px; border-radius:8px; margin-bottom:15px; 
                    box-shadow:0 2px 6px rgba(0,0,0,0.08);">
          <p style="margin:0; font-size:16px; color:#34495e;">
            <b>{flight['departure_airport']}</b> → <b>{flight['arrival_airport']}</b>
          </p>
          <p style="margin:5px 0; font-size:14px; color:#555;">
            🕑 {dep_time} → {arr_time}
          </p>
        """

        if stops:
            body += "<p style='margin:5px 0; font-size:13px; color:#888;'>Stops:</p><ul style='margin:0; padding-left:20px;'>"
            for stop in stops:
                body += f"<li>{stop['airport']} ({stop['duration']})</li>"
            body += "</ul>"
        else:
            body += "<p style='margin:5px 0; font-size:13px; color:#27ae60;'>Direct flight ✅</p>"

        body += "</div>"

    body += "</body></html>"
    return body


def _format_datetime(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%a, %d %b %Y %H:%M")
    except Exception:
        return dt_str

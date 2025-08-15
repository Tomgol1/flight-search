def build_email_body(flights):
    """
    flights: list of dicts, each with keys:
        - price
        - origin
        - destination
        - departure_date
        - return_date
        - departure_time
        - arrival_time
        - stopovers (list of dicts: {"location": str, "duration": str})
    """
    if not flights:
        return "<p>No flights found matching your criteria.</p>"

    html = """
    <html>
    <head>
      <style>
        body { font-family: Arial, sans-serif; background-color: #f9f9f9; }
        .flight-card {
          background: #fff;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          margin: 20px auto;
          padding: 20px;
          max-width: 600px;
        }
        .price { font-size: 22px; font-weight: bold; color: #1a73e8; }
        .route { font-size: 18px; margin-top: 8px; }
        .times { margin: 12px 0; }
        .stop { font-size: 14px; color: #555; margin-top: 4px; }
      </style>
    </head>
    <body>
      <h2 style="text-align:center; color:#333;">✈️ Flight Search Results</h2>
    """

    for flight in flights:
        stops_html = ""
        if flight.get("stopovers"):
            stops_html = "<div><b>Stopovers:</b></div>"
            for s in flight["stopovers"]:
                stops_html += f"<div class='stop'>• {s['location']} ({s['duration']})</div>"
        else:
            stops_html = "<div class='stop'>Direct flight</div>"

        html += f"""
        <div class="flight-card">
          <div class="price">{flight['price']}</div>
          <div class="route">{flight['origin']} → {flight['destination']}</div>
          <div class="times">
            <b>Departure:</b> {flight['departure_date']} at {flight['departure_time']}<br>
            <b>Arrival:</b> {flight['return_date']} at {flight['arrival_time']}
          </div>
          {stops_html}
        </div>
        """

    html += "</body></html>"
    return html

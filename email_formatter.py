def build_email_body(*flights):
    """
    Build a polished HTML email body for multiple flight options.
    Each flight is passed as a dictionary.
    """
    if not flights:
        return "<p>No flights found matching your criteria.</p>"

    email_html = """
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f4f4f7;
                color: #333;
            }
            h2 {
                color: #2c3e50;
                text-align: center;
            }
            .flight-card {
                background: #fff;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                margin: 20px auto;
                padding: 20px;
                max-width: 600px;
                border-left: 6px solid #3498db;
            }
            .flight-header {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
                color: #3498db;
            }
            .flight-detail {
                margin: 6px 0;
                font-size: 14px;
            }
            .highlight {
                font-weight: bold;
                color: #2c3e50;
            }
            .price {
                font-size: 18px;
                font-weight: bold;
                color: #27ae60;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <h2>Flight Search Results</h2>
    """

    for idx, flight in enumerate(flights, start=1):
        email_html += f"""
        <div class="flight-card">
            <div class="flight-header">Option {idx}</div>
            <div class="flight-detail"><span class="highlight">From:</span> {flight.get('origin')}</div>
            <div class="flight-detail"><span class="highlight">To:</span> {flight.get('destination')}</div>
            <div class="flight-detail"><span class="highlight">Departure:</span> {flight.get('departure_time')}</div>
            <div class="flight-detail"><span class="highlight">Arrival:</span> {flight.get('arrival_time')}</div>
            <div class="flight-detail"><span class="highlight">Duration:</span> {flight.get('duration')}</div>
            <div class="flight-detail"><span class="highlight">Stops:</span> {flight.get('stops')}</div>
            <div class="price">Price: {flight.get('price')}</div>
        </div>
        """

    email_html += """
    </body>
    </html>
    """

    return email_html

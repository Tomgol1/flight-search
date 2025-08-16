from datetime import datetime

def _format_datetime(dt_str):
    """Format ISO datetime to readable format"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%a, %b %d - %H:%M")
    except Exception:
        return dt_str

def _format_duration(duration_str):
    """Convert PT4H30M to '4h 30m' format"""
    try:
        import re
        duration_str = duration_str.replace('PT', '')
        
        hours = 0
        minutes = 0
        
        hour_match = re.search(r'(\d+)H', duration_str)
        if hour_match:
            hours = int(hour_match.group(1))
        
        min_match = re.search(r'(\d+)M', duration_str)
        if min_match:
            minutes = int(min_match.group(1))
        
        if hours and minutes:
            return f"{hours}h {minutes}m"
        elif hours:
            return f"{hours}h"
        elif minutes:
            return f"{minutes}m"
        else:
            return duration_str
    except Exception:
        return duration_str

def _get_airline_name(carrier_code):
    """Convert airline code to readable name"""
    airline_names = {
        'LH': 'Lufthansa',
        'BA': 'British Airways',
        'AF': 'Air France',
        'KL': 'KLM',
        'TK': 'Turkish Airlines',
        'EK': 'Emirates',
        'QR': 'Qatar Airways',
        'LY': 'El Al',
        'W6': 'Wizz Air',
        'FR': 'Ryanair',
        'U2': 'easyJet',
        'OS': 'Austrian Airlines',
        'LX': 'Swiss',
        'SN': 'Brussels Airlines',
        'AY': 'Finnair',
        'SK': 'SAS',
        'IB': 'Iberia',
        'VY': 'Vueling',
        'TP': 'TAP Portugal',
        'UX': 'Air Europa'
    }
    return airline_names.get(carrier_code, carrier_code)

def build_email_body(flights, departure_dates, return_dates, ai_summary, origin, destination):
    """
    Build a well-formatted HTML email body with flight results
    """
    if not flights:
        return """
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#f8f9fa; padding:20px; color:#333;">
            <div style="max-width:800px; margin:auto; background:white; border-radius:10px; padding:30px; box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                <h2 style="text-align:center; color:#e74c3c; margin-bottom:20px;">✈️ No Flights Found</h2>
                <p style="text-align:center; font-size:16px;">No flights available for your search criteria.</p>
            </div>
        </body>
        </html>
        """

    # Get currency from first flight
    currency = flights[0]['price']['currency']
    
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:1.6;">
        <div style="max-width:900px; margin:auto; background:white; border-radius:12px; overflow:hidden; box-shadow:0 6px 20px rgba(0,0,0,0.1);">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding:30px; text-align:center; color:white;">
                <h1 style="margin:0; font-size:28px; font-weight:300;">✈️ Flight Search Results</h1>
                <p style="margin:10px 0 0 0; font-size:18px; opacity:0.9;">
                    <strong>{origin}</strong> → <strong>{destination}</strong>
                </p>
                <p style="margin:5px 0 0 0; font-size:14px; opacity:0.8;">
                    Found {len(flights)} flight options • All prices in {currency}
                </p>
            </div>

            <!-- AI Summary Section -->
            <div style="padding:30px; border-bottom:2px solid #f1f3f4;">
                <h2 style="color:#4a5568; margin:0 0 20px 0; font-size:22px; font-weight:600;">
                    🤖 AI Flight Analysis
                </h2>
                <div style="background:#f7fafc; padding:20px; border-radius:8px; border-left:4px solid #667eea;">
                    {ai_summary}
                </div>
            </div>

            <!-- Flight Options -->
            <div style="padding:30px;">
                <h2 style="color:#4a5568; margin:0 0 25px 0; font-size:22px; font-weight:600;">
                    📋 All Flight Options
                </h2>
    """

    for idx, flight in enumerate(flights, start=1):
        dep_seg = flight['itineraries'][0]['segments'][0]
        arr_seg = flight['itineraries'][0]['segments'][-1]
        
        # Extract flight details
        airline_code = dep_seg['carrierCode']
        airline_name = _get_airline_name(airline_code)
        flight_number = dep_seg['number']
        
        dep_airport = dep_seg['departure']['iataCode']
        arr_airport = arr_seg['arrival']['iataCode']
        dep_time = _format_datetime(dep_seg['departure']['at'])
        arr_time = _format_datetime(arr_seg['arrival']['at'])
        
        duration = _format_duration(flight['itineraries'][0]['duration'])
        price = flight['price']['total']
        stops = len(flight['itineraries'][0]['segments']) - 1
        
        # Determine stops text and color
        if stops == 0:
            stops_text = "Direct"
            stops_color = "#10b981"  # green
        elif stops == 1:
            stops_text = "1 Stop"
            stops_color = "#f59e0b"  # yellow
        else:
            stops_text = f"{stops} Stops"
            stops_color = "#ef4444"  # red

        # Create flight card
        html += f"""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; margin-bottom:20px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                    
                    <!-- Flight Header -->
                    <div style="background:#f8fafc; padding:15px 20px; border-bottom:1px solid #e2e8f0;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="font-weight:700; font-size:18px; color:#2d3748;">Option {idx}</span>
                                <span style="margin-left:10px; color:#718096; font-size:14px;">{airline_name} {flight_number}</span>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:24px; font-weight:700; color:#2d3748;">{price} {currency}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Flight Details -->
                    <div style="padding:20px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                            <div style="text-align:center; flex:1;">
                                <div style="font-size:20px; font-weight:600; color:#2d3748;">{dep_airport}</div>
                                <div style="font-size:14px; color:#718096; margin-top:2px;">{dep_time}</div>
                            </div>
                            
                            <div style="flex:1; text-align:center; padding:0 20px;">
                                <div style="border-top:2px solid #cbd5e0; position:relative; margin:10px 0;">
                                    <span style="background:white; padding:0 10px; position:absolute; top:-10px; left:50%; transform:translateX(-50%); font-size:12px; color:#718096;">
                                        {duration}
                                    </span>
                                </div>
                                <div style="margin-top:5px;">
                                    <span style="background-color:{stops_color}; color:white; padding:4px 8px; border-radius:12px; font-size:12px; font-weight:600;">
                                        {stops_text}
                                    </span>
                                </div>
                            </div>
                            
                            <div style="text-align:center; flex:1;">
                                <div style="font-size:20px; font-weight:600; color:#2d3748;">{arr_airport}</div>
                                <div style="font-size:14px; color:#718096; margin-top:2px;">{arr_time}</div>
                            </div>
                        </div>
                        
                        <!-- Booking Link -->
                        <div style="text-align:center; margin-top:20px;">
                            <a href="https://www.kayak.com/flights/{dep_airport}-{arr_airport}" 
                               style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:12px 24px; text-decoration:none; border-radius:25px; font-weight:600; font-size:14px; display:inline-block;">
                                🔗 Search on Kayak
                            </a>
                        </div>
                    </div>
                </div>
        """

    html += """
            </div>
            
            <!-- Footer -->
            <div style="background:#f8fafc; padding:20px; text-align:center; border-top:1px solid #e2e8f0;">
                <p style="margin:0; color:#718096; font-size:14px;">
                    🤖 Automated flight search • Times shown in departure timezone
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return html

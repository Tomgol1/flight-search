from datetime import datetime
import logging
import re

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

def _calculate_layover_duration(arrival_time, departure_time):
    """Calculate layover duration between two flights"""
    try:
        arr_dt = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
        dep_dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
        
        layover_duration = dep_dt - arr_dt
        total_minutes = int(layover_duration.total_seconds() / 60)
        
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours and minutes:
            return f"{hours}h {minutes}m"
        elif hours:
            return f"{hours}h"
        elif minutes:
            return f"{minutes}m"
        else:
            return "0m"
    except Exception:
        return "Unknown"

def get_airline_name_from_amadeus(amadeus_client, carrier_code):
    """Get airline name using Amadeus API"""
    try:
        response = amadeus_client.reference_data.airlines.get(airlineCodes=carrier_code)
        if response.data:
            return response.data[0]['businessName']
    except Exception as e:
        logging.debug(f"Could not fetch airline name for {carrier_code}: {e}")
    return None

def get_airport_name_from_amadeus(amadeus_client, airport_code):
    """Get airport name using Amadeus API"""
    try:
        response = amadeus_client.reference_data.locations.get(
            keyword=airport_code,
            subType='AIRPORT'
        )
        if response.data:
            for location in response.data:
                if location['iataCode'] == airport_code:
                    return location['name']
    except Exception as e:
        logging.debug(f"Could not fetch airport name for {airport_code}: {e}")
    return None

def _get_airline_name(carrier_code, amadeus_client=None):
    """Convert airline code to readable name, with API fallback"""
    
    # Try API first if available
    if amadeus_client:
        api_name = get_airline_name_from_amadeus(amadeus_client, carrier_code)
        if api_name:
            return api_name
    
    # Fallback to static mapping
    airline_names = {
        'LH': 'Lufthansa',
        'BA': 'British Airways',
        'AF': 'Air France',
        'KL': 'KLM Royal Dutch Airlines',
        'TK': 'Turkish Airlines',
        'EK': 'Emirates',
        'QR': 'Qatar Airways',
        'LY': 'El Al Israel Airlines',
        'W6': 'Wizz Air',
        'FR': 'Ryanair',
        'U2': 'easyJet',
        'OS': 'Austrian Airlines',
        'LX': 'Swiss International Air Lines',
        'SN': 'Brussels Airlines',
        'AY': 'Finnair',
        'SK': 'Scandinavian Airlines',
        'IB': 'Iberia',
        'VY': 'Vueling',
        'TP': 'TAP Air Portugal',
        'UX': 'Air Europa',
        'DL': 'Delta Air Lines',
        'AA': 'American Airlines',
        'UA': 'United Airlines',
        'AC': 'Air Canada',
        'VS': 'Virgin Atlantic',
        'WF': 'Widerøe',
        'FI': 'Icelandair',
        '6H': 'Israir Airlines',
        'UP': 'Bahamasair'
    }
    return airline_names.get(carrier_code, carrier_code)

def _get_airport_name(airport_code, amadeus_client=None):
    """Convert airport code to readable name, with API fallback"""
    
    # Try API first if available
    if amadeus_client:
        api_name = get_airport_name_from_amadeus(amadeus_client, airport_code)
        if api_name:
            return api_name
    
    # Fallback to static mapping for common airports
    airport_names = {
        'TLV': 'Ben Gurion Airport, Tel Aviv',
        'KEF': 'Keflavik International Airport, Reykjavik',
        'LHR': 'Heathrow Airport, London',
        'CDG': 'Charles de Gaulle Airport, Paris',
        'FRA': 'Frankfurt Airport',
        'AMS': 'Amsterdam Schiphol Airport',
        'IST': 'Istanbul Airport',
        'DXB': 'Dubai International Airport',
        'DOH': 'Hamad International Airport, Doha',
        'VIE': 'Vienna International Airport',
        'ZUR': 'Zurich Airport',
        'BRU': 'Brussels Airport',
        'HEL': 'Helsinki Airport',
        'ARN': 'Stockholm Arlanda Airport',
        'MAD': 'Madrid-Barajas Airport',
        'BCN': 'Barcelona Airport',
        'LIS': 'Lisbon Airport',
        'JFK': 'John F. Kennedy International Airport, New York',
        'LAX': 'Los Angeles International Airport',
        'ORD': 'O\'Hare International Airport, Chicago'
    }
    return airport_names.get(airport_code, f"{airport_code} Airport")

def _get_stop_information(segments):
    """Extract detailed stop information from flight segments"""
    if len(segments) <= 1:
        return []
    
    stops = []
    for i in range(len(segments) - 1):
        current_segment = segments[i]
        next_segment = segments[i + 1]
        
        stop_airport = current_segment['arrival']['iataCode']
        arrival_time = current_segment['arrival']['at']
        departure_time = next_segment['departure']['at']
        layover_duration = _calculate_layover_duration(arrival_time, departure_time)
        
        stops.append({
            'airport': stop_airport,
            'duration': layover_duration
        })
    
    return stops

def build_email_body(flights, departure_dates, return_dates, ai_summary, origin, destination, amadeus_client=None):
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

    # Get currency - but display as USD since you mentioned all prices are USD
    currency_code = flights[0]['price']['currency']
    
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
                    <strong>{_get_airport_name(origin, amadeus_client)}</strong> → <strong>{_get_airport_name(destination, amadeus_client)}</strong>
                </p>
                <p style="margin:5px 0 0 0; font-size:14px; opacity:0.8;">
                    Found {len(flights)} flight options • All prices in USD
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
        segments = flight['itineraries'][0]['segments']
        dep_seg = segments[0]
        arr_seg = segments[-1]
        
        # Extract flight details
        airline_code = dep_seg['carrierCode']
        airline_name = _get_airline_name(airline_code, amadeus_client)
        flight_number = dep_seg['number']
        
        dep_airport = dep_seg['departure']['iataCode']
        arr_airport = arr_seg['arrival']['iataCode']
        dep_time = _format_datetime(dep_seg['departure']['at'])
        arr_time = _format_datetime(arr_seg['arrival']['at'])
        
        duration = _format_duration(flight['itineraries'][0]['duration'])
        price = flight['price']['total']
        stops_info = _get_stop_information(segments)
        stops_count = len(stops_info)
        
        # Determine stops text and color
        if stops_count == 0:
            stops_text = "Direct"
            stops_color = "#10b981"  # green
            stops_detail = ""
        elif stops_count == 1:
            stop = stops_info[0]
            stops_text = "1 Stop"
            stops_color = "#f59e0b"  # yellow
            stops_detail = f"<br><small style='color:#718096;'>via {_get_airport_name(stop['airport'], amadeus_client)} ({stop['duration']} layover)</small>"
        else:
            stops_text = f"{stops_count} Stops"
            stops_color = "#ef4444"  # red
            stop_airports = [_get_airport_name(stop['airport'], amadeus_client).split(',')[0] for stop in stops_info]
            stops_detail = f"<br><small style='color:#718096;'>via {', '.join(stop_airports)}</small>"

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
                                <div style="font-size:24px; font-weight:700; color:#2d3748;">${price}</div>
                                <div style="font-size:12px; color:#718096;">USD</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Flight Details -->
                    <div style="padding:20px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                            <div style="text-align:center; flex:1;">
                                <div style="font-size:20px; font-weight:600; color:#2d3748;">{dep_airport}</div>
                                <div style="font-size:14px; color:#718096; margin-top:2px;">{dep_time}</div>
                                <div style="font-size:12px; color:#a0aec0; margin-top:2px;">{_get_airport_name(dep_airport, amadeus_client).split(',')[0]}</div>
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
                                    {stops_detail}
                                </div>
                            </div>
                            
                            <div style="text-align:center; flex:1;">
                                <div style="font-size:20px; font-weight:600; color:#2d3748;">{arr_airport}</div>
                                <div style="font-size:14px; color:#718096; margin-top:2px;">{arr_time}</div>
                                <div style="font-size:12px; color:#a0aec0; margin-top:2px;">{_get_airport_name(arr_airport, amadeus_client).split(',')[0]}</div>
                            </div>
                        </div>
        """

        # Add detailed stop information if there are stops
        if stops_info:
            html += """
                        <div style="margin-top:20px; padding-top:15px; border-top:1px solid #e2e8f0;">
                            <h4 style="margin:0 0 10px 0; color:#4a5568; font-size:14px;">✈️ Stop Details:</h4>
            """
            for i, stop in enumerate(stops_info):
                airport_name = _get_airport_name(stop['airport'], amadeus_client)
                html += f"""
                            <div style="margin-bottom:8px; padding:8px 12px; background:#f7fafc; border-radius:6px; font-size:13px;">
                                <strong>{stop['airport']}</strong> - {airport_name.split(',')[0]} 
                                <span style="color:#718096;">({stop['duration']} layover)</span>
                            </div>
                """
            html += "</div>"

        html += f"""
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
                    🤖 Automated flight search • Times shown in local timezone • Powered by Amadeus API
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return html

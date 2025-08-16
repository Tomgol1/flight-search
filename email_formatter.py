from datetime import datetime
import logging
import re
from cache_manager import cache

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
    Build a well-formatted HTML email body with improved design
    """
    if not flights:
        return """
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background:#f5f7fa; margin:0; padding:20px;">
            <div style="max-width:700px; margin:0 auto; background:white; border-radius:16px; box-shadow:0 4px 24px rgba(0,0,0,0.08); overflow:hidden;">
                <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding:40px; text-align:center; color:white;">
                    <h1 style="margin:0; font-size:32px; font-weight:600;">✈️ No Flights Found</h1>
                    <p style="margin:16px 0 0; font-size:16px; opacity:0.9;">No flights available for your search criteria.</p>
                </div>
            </div>
        </body>
        </html>
        """

    # Get origin and destination airport names using cache
    origin_name = cache.get_airport_name(origin, amadeus_client)
    destination_name = cache.get_airport_name(destination, amadeus_client)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }}
        </style>
    </head>
    <body style="margin:0; padding:20px; background:#f5f7fa; color:#1f2937;">
        <div style="max-width:700px; margin:0 auto; background:white; border-radius:16px; box-shadow:0 4px 24px rgba(0,0,0,0.08); overflow:hidden;">
            
            <!-- Header -->
            <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding:40px; text-align:center; color:white;">
                <h1 style="margin:0; font-size:32px; font-weight:600;">✈️ Flight Search Results</h1>
                <div style="margin:20px 0; font-size:18px; font-weight:500;">
                    {origin_name.split(',')[0]} → {destination_name.split(',')[0]}
                </div>
                <div style="font-size:14px; opacity:0.8;">
                    {len(flights)} options found • All prices in USD
                </div>
            </div>

            <!-- AI Summary -->
            <div style="padding:32px;">
                <div style="background:linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); border-radius:12px; padding:24px; margin-bottom:32px;">
                    <h2 style="margin:0 0 16px; font-size:18px; font-weight:600; color:#374151;">🤖 AI Flight Analysis</h2>
                    <div style="color:#4b5563; line-height:1.6;">
                        {ai_summary}
                    </div>
                </div>
                
                <h2 style="margin:0 0 24px; font-size:20px; font-weight:600; color:#374151;">Flight Options</h2>
    """

    for idx, flight in enumerate(flights, start=1):
        segments = flight['itineraries'][0]['segments']
        dep_seg = segments[0]
        arr_seg = segments[-1]
        
        # Extract flight details using cache
        airline_code = dep_seg['carrierCode']
        airline_name = cache.get_airline_name(airline_code, amadeus_client)
        flight_number = dep_seg['number']
        
        dep_airport = dep_seg['departure']['iataCode']
        arr_airport = arr_seg['arrival']['iataCode']
        dep_time = _format_datetime(dep_seg['departure']['at'])
        arr_time = _format_datetime(arr_seg['arrival']['at'])
        
        duration = _format_duration(flight['itineraries'][0]['duration'])
        price = float(flight['price']['total'])
        stops_info = _get_stop_information(segments)
        stops_count = len(stops_info)
        
        # Format price nicely
        price_display = f"${price:,.2f}".replace('.00', '')
        
        # Determine stops styling
        if stops_count == 0:
            stops_badge = f'<span style="background:#10b981; color:white; padding:6px 12px; border-radius:20px; font-size:12px; font-weight:600;">Direct</span>'
            stops_detail = ""
        else:
            stop_color = "#f59e0b" if stops_count == 1 else "#ef4444"
            stops_text = f"{stops_count} Stop{'s' if stops_count > 1 else ''}"
            stops_badge = f'<span style="background:{stop_color}; color:white; padding:6px 12px; border-radius:20px; font-size:12px; font-weight:600;">{stops_text}</span>'
            
            if stops_count == 1:
                stop = stops_info[0]
                stop_name = cache.get_airport_name(stop['airport'], amadeus_client).split(',')[0]
                stops_detail = f'<div style="font-size:13px; color:#6b7280; margin-top:8px;">via {stop_name} ({stop["duration"]} layover)</div>'
            else:
                stop_names = [cache.get_airport_name(stop['airport'], amadeus_client).split(',')[0] for stop in stops_info]
                stops_detail = f'<div style="font-size:13px; color:#6b7280; margin-top:8px;">via {", ".join(stop_names)}</div>'

        # Create flight card with improved design
        html += f"""
                <div style="border:1px solid #e5e7eb; border-radius:12px; margin-bottom:20px; background:white; box-shadow:0 1px 3px rgba(0,0,0,0.1);">
                    
                    <!-- Flight Header -->
                    <div style="background:#f9fafb; padding:20px; border-radius:12px 12px 0 0; border-bottom:1px solid #e5e7eb; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:700; font-size:16px; color:#111827;">Option {idx}</div>
                            <div style="font-size:13px; color:#6b7280; margin-top:2px;">
                                {airline_name} {flight_number}
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:24px; font-weight:700; color:#111827;">{price_display}</div>
                            <div style="font-size:11px; color:#6b7280; font-weight:500;">USD</div>
                        </div>
                    </div>
                    
                    <!-- Flight Route -->
                    <div style="padding:24px;">
                        <div style="display:flex; align-items:center; margin-bottom:20px;">
                            
                            <!-- Departure -->
                            <div style="flex:1; text-align:center;">
                                <div style="font-size:28px; font-weight:700; color:#111827; letter-spacing:-0.5px;">{dep_airport}</div>
                                <div style="font-size:14px; color:#374151; margin:4px 0;">{dep_time}</div>
                                <div style="font-size:12px; color:#9ca3af;">
                                    {cache.get_airport_name(dep_airport, amadeus_client).split(',')[0]}
                                </div>
                            </div>
                            
                            <!-- Flight Path -->
                            <div style="flex:2; text-align:center; padding:0 24px;">
                                <div style="position:relative; margin:16px 0;">
                                    <div style="border-top:2px solid #d1d5db; position:relative;">
                                        <div style="position:absolute; top:-8px; left:50%; transform:translateX(-50%); background:white; padding:0 12px; font-size:12px; color:#6b7280; font-weight:500;">
                                            {duration}
                                        </div>
                                    </div>
                                </div>
                                <div style="margin-top:12px;">
                                    {stops_badge}
                                    {stops_detail}
                                </div>
                            </div>
                            
                            <!-- Arrival -->
                            <div style="flex:1; text-align:center;">
                                <div style="font-size:28px; font-weight:700; color:#111827; letter-spacing:-0.5px;">{arr_airport}</div>
                                <div style="font-size:14px; color:#374151; margin:4px 0;">{arr_time}</div>
                                <div style="font-size:12px; color:#9ca3af;">
                                    {cache.get_airport_name(arr_airport, amadeus_client).split(',')[0]}
                                </div>
                            </div>
                            
                        </div>
        """

        # Add detailed stop information if there are stops
        if stops_info:
            html += '''
                        <div style="background:#f9fafb; border-radius:8px; padding:16px; margin:20px 0;">
                            <div style="font-weight:600; color:#374151; font-size:14px; margin-bottom:12px;">✈️ Stop Details</div>
            '''
            for stop in stops_info:
                airport_name = cache.get_airport_name(stop['airport'], amadeus_client)
                html += f'''
                            <div style="background:white; border:1px solid #e5e7eb; border-radius:6px; padding:12px; margin-bottom:8px; font-size:13px;">
                                <strong style="color:#111827;">{stop['airport']}</strong> - {airport_name.split(',')[0]}
                                <span style="color:#6b7280;">({stop['duration']} layover)</span>
                            </div>
                '''
            html += '</div>'

        # Booking button
        html += f'''
                        <div style="text-align:center; margin-top:20px;">
                            <a href="https://www.kayak.com/flights/{dep_airport}-{arr_airport}" 
                               style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:14px 28px; text-decoration:none; border-radius:25px; font-weight:600; font-size:14px; display:inline-block; box-shadow:0 2px 8px rgba(102, 126, 234, 0.3);">
                                🔗 Search on Kayak
                            </a>
                        </div>
                    </div>
                </div>
        '''

    # Footer with cache stats
    cache_stats = cache.get_cache_stats()
    html += f"""
            </div>
            
            <!-- Footer -->
            <div style="background:#f9fafb; padding:24px; text-align:center; border-top:1px solid #e5e7eb;">
                <div style="color:#6b7280; font-size:13px; line-height:1.5;">
                    🤖 Automated flight search powered by Amadeus API<br>
                    <span style="font-size:11px;">Cache: {cache_stats['airlines_cached']} airlines, {cache_stats['airports_cached']} airports stored</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return html

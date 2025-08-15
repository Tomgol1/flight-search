from datetime import datetime
from flight_search import ORIGIN, DESTINATION, build_search_link  # import build_search_link if needed

def build_email_body(flights, departure_dates, return_dates, summary):
    html = """
    <html>
    <head>
      <style>
        table {border-collapse: collapse; width: 100%;}
        th, td {border: 1px solid #ddd; padding: 8px;}
        th {background-color: #f2f2f2; text-align: left;}
        tr:hover {background-color: #f9f9f9;}
      </style>
    </head>
    <body>
      <h2>Flight Search Results</h2>
      <table>
        <tr>
          <th>Airline</th>
          <th>Segment</th>
          <th>Departure</th>
          <th>Arrival</th>
          <th>Duration</th>
          <th>Stopover</th>
          <th>Price</th>
        </tr>
    """

    for f in flights:
        itinerary = f["itineraries"][0]
        segments = itinerary["segments"]
        price = f["price"]["total"]
        carrier = segments[0]["carrierCode"]

        for i, seg in enumerate(segments):
            dep_airport = seg["departure"]["iataCode"]
            dep_time = seg["departure"]["at"]
            arr_airport = seg["arrival"]["iataCode"]
            arr_time = seg["arrival"]["at"]
            duration = seg.get("duration", "N/A")

            stopover = "—"
            if i < len(segments) - 1:
                next_dep_time = segments[i+1]["departure"]["at"]
                try:
                    stop_duration = datetime.fromisoformat(next_dep_time) - datetime.fromisoformat(arr_time)
                    stopover = str(stop_duration)
                except Exception:
                    stopover = "N/A"

            html += f"""
            <tr>
              <td>{carrier}</td>
              <td>{i+1}</td>
              <td>{dep_airport} ({dep_time})</td>
              <td>{arr_airport} ({arr_time})</td>
              <td>{duration}</td>
              <td>{stopover}</td>
              <td>${price}</td>
            </tr>
            """

    html += "<tr><td colspan='7'><b>Flight Search Links:</b><br>"
    for dep in departure_dates:
        for ret in return_dates:
            link = build_search_link(ORIGIN, DESTINATION, dep, ret)
            html += f'<a href="{link}">{dep} → {ret}</a><br>'
    html += "</td></tr>"

    html += f"""
      </table>
      <h3>AI Summary</h3>
      <p>{summary}</p>
    </body>
    </html>
    """
    return html

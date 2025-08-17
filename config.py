# config.py

# Flight search settings
ORIGIN = "TLV"             # city or airport code
DESTINATION = "KEF"        # city or airport code
DEPARTURE_DATE = "2026-08-11"
RETURN_DATE = "2026-08-12"
ALLOW_DEPARTURE_NEXT_DAY = True   # Search departure date +1 day
ALLOW_RETURN_NEXT_DAY = True      # Search return date +1 day
MAX_RESULTS = 20
MAX_STOPS = 2              # Maximum number of stops (0=direct only, 1=max 1 stop, 2=max 2 stops, etc.)

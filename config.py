# config.py

# Flight search settings
ORIGIN = "TLV"             # city or airport code
DESTINATION = "KEF"        # city or airport code
DEPARTURE_DATE = "2026-01-11"
RETURN_DATE = "2026-01-12"
ALLOW_DEPARTURE_NEXT_DAY = False   # Search departure date +1 day
ALLOW_RETURN_NEXT_DAY = False      # Search return date +1 day
MAX_RESULTS = 10
MAX_STOPS = 1              # Maximum number of stops (0=direct only, 1=max 1 stop, 2=max 2 stops, etc.)

import json
import os
import logging
from datetime import datetime, timedelta

class AirportAirlineCache:
    def __init__(self, cache_file="airport_airline_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.cache_updated = False  # Track if cache was modified
    
    def _load_cache(self):
        """Load cache from file or create new cache"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    # Check if cache is old format, migrate if needed
                    if 'airlines' not in cache_data or 'airports' not in cache_data:
                        logging.info("Migrating old cache format")
                        return self._create_empty_cache()
                    
                    # Log cache restoration
                    airlines_count = len(cache_data.get('airlines', {}))
                    airports_count = len(cache_data.get('airports', {}))
                    last_updated = cache_data.get('last_updated', 'unknown')
                    logging.info(f"Cache restored: {airlines_count} airlines, {airports_count} airports (last updated: {last_updated})")
                    
                    return cache_data
            except Exception as e:
                logging.warning(f"Could not load cache file: {e}. Creating new cache.")
                return self._create_empty_cache()
        else:
            logging.info("No existing cache found, creating new cache")
            return self._create_empty_cache()
    
    def _create_empty_cache(self):
        """Create empty cache structure"""
        return {
            'airlines': {}, 
            'airports': {}, 
            'last_updated': datetime.now().isoformat(),
            'version': '1.0'
        }
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            self.cache['last_updated'] = datetime.now().isoformat()
            self.cache['version'] = '1.0'
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.cache_file) if os.path.dirname(self.cache_file) else '.', exist_ok=True)
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            
            logging.debug(f"Cache saved to {self.cache_file}")
            self.cache_updated = True
            
        except Exception as e:
            logging.error(f"Could not save cache: {e}")
    
    def get_airline_name(self, carrier_code, amadeus_client=None):
        """Get airline name from cache or API"""
        if carrier_code in self.cache['airlines']:
            logging.debug(f"Airline {carrier_code} found in cache")
            return self.cache['airlines'][carrier_code]
        
        # Try API if client provided
        if amadeus_client:
            try:
                response = amadeus_client.reference_data.airlines.get(airlineCodes=carrier_code)
                if response.data:
                    airline_name = response.data[0]['businessName']
                    # Cache the result
                    self.cache['airlines'][carrier_code] = airline_name
                    self._save_cache()
                    logging.info(f"Cached new airline {carrier_code}: {airline_name}")
                    return airline_name
            except Exception as e:
                logging.debug(f"Could not fetch airline {carrier_code} from API: {e}")
        
        # Fallback to static mapping
        return self._get_airline_fallback(carrier_code)
    
    def get_airport_name(self, airport_code, amadeus_client=None):
        """Get airport name from cache or API"""
        if airport_code in self.cache['airports']:
            logging.debug(f"Airport {airport_code} found in cache")
            return self.cache['airports'][airport_code]
        
        # Try API if client provided
        if amadeus_client:
            try:
                response = amadeus_client.reference_data.locations.get(
                    keyword=airport_code,
                    subType='AIRPORT'
                )
                if response.data:
                    for location in response.data:
                        if location['iataCode'] == airport_code:
                            airport_name = location['name']
                            # Cache the result
                            self.cache['airports'][airport_code] = airport_name
                            self._save_cache()
                            logging.info(f"Cached new airport {airport_code}: {airport_name}")
                            return airport_name
            except Exception as e:
                logging.debug(f"Could not fetch airport {airport_code} from API: {e}")
        
        # Fallback to static mapping
        return self._get_airport_fallback(airport_code)
    
    def _get_airline_fallback(self, carrier_code):
        """Static airline mapping as fallback"""
        airline_names = {
            'LH': 'Lufthansa', 'BA': 'British Airways', 'AF': 'Air France',
            'KL': 'KLM Royal Dutch Airlines', 'TK': 'Turkish Airlines', 'EK': 'Emirates',
            'QR': 'Qatar Airways', 'LY': 'El Al Israel Airlines', 'W6': 'Wizz Air',
            'FR': 'Ryanair', 'U2': 'easyJet', 'OS': 'Austrian Airlines',
            'LX': 'Swiss International Air Lines', 'SN': 'Brussels Airlines',
            'AY': 'Finnair', 'SK': 'Scandinavian Airlines', 'IB': 'Iberia',
            'VY': 'Vueling', 'TP': 'TAP Air Portugal', 'UX': 'Air Europa',
            'DL': 'Delta Air Lines', 'AA': 'American Airlines', 'UA': 'United Airlines',
            'AC': 'Air Canada', 'VS': 'Virgin Atlantic', 'WF': 'Widerøe',
            'FI': 'Icelandair', '6H': 'Israir Airlines', 'UP': 'Bahamasair',
            'EL': 'El Al Israel Airlines'  # Added EL Al alternative code
        }
        name = airline_names.get(carrier_code, f"{carrier_code} Airlines")
        
        # Only cache fallback if it's a known airline
        if carrier_code in airline_names:
            self.cache['airlines'][carrier_code] = name
            self._save_cache()
            logging.debug(f"Cached fallback airline {carrier_code}: {name}")
        
        return name
    
    def _get_airport_fallback(self, airport_code):
        """Static airport mapping as fallback"""
        airport_names = {
            'TLV': 'Ben Gurion Airport, Tel Aviv', 
            'KEF': 'Keflavik International Airport, Reykjavik',
            'LHR': 'Heathrow Airport, London', 
            'CDG': 'Charles de Gaulle Airport, Paris',
            'FRA': 'Frankfurt Airport, Frankfurt', 
            'AMS': 'Amsterdam Schiphol Airport, Amsterdam',
            'IST': 'Istanbul Airport, Istanbul', 
            'DXB': 'Dubai International Airport, Dubai',
            'DOH': 'Hamad International Airport, Doha', 
            'VIE': 'Vienna International Airport, Vienna',
            'ZUR': 'Zurich Airport, Zurich', 
            'BRU': 'Brussels Airport, Brussels', 
            'HEL': 'Helsinki Airport, Helsinki',
            'ARN': 'Stockholm Arlanda Airport, Stockholm', 
            'MAD': 'Madrid-Barajas Airport, Madrid',
            'BCN': 'Barcelona Airport, Barcelona', 
            'LIS': 'Lisbon Airport, Lisbon',
            'JFK': 'John F. Kennedy International Airport, New York',
            'LAX': 'Los Angeles International Airport, Los Angeles',
            'ORD': 'O\'Hare International Airport, Chicago',
            'CPH': 'Copenhagen Airport, Copenhagen',
            'OSL': 'Oslo Airport, Oslo',
            'MUC': 'Munich Airport, Munich',
            'FCO': 'Leonardo da Vinci Airport, Rome'
        }
        name = airport_names.get(airport_code, f"{airport_code} Airport")
        
        # Only cache fallback if it's a known airport
        if airport_code in airport_names:
            self.cache['airports'][airport_code] = name
            self._save_cache()
            logging.debug(f"Cached fallback airport {airport_code}: {name}")
        
        return name
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return {
            'airlines_cached': len(self.cache['airlines']),
            'airports_cached': len(self.cache['airports']),
            'last_updated': self.cache['last_updated'],
            'cache_updated_this_run': self.cache_updated
        }
    
    def preload_common_data(self):
        """Preload common airports and airlines to reduce API calls"""
        common_airlines = ['LH', 'BA', 'AF', 'KL', 'TK', 'EK', 'QR', 'LY', 'W6', 'FR', 'U2', 'OS', 'LX', 'SN', 'AY', 'SK', 'FI', 'EL']
        common_airports = ['TLV', 'KEF', 'LHR', 'CDG', 'FRA', 'AMS', 'IST', 'DXB', 'VIE', 'ZUR', 'CPH', 'OSL']
        
        for airline in common_airlines:
            if airline not in self.cache['airlines']:
                self._get_airline_fallback(airline)
        
        for airport in common_airports:
            if airport not in self.cache['airports']:
                self._get_airport_fallback(airport)
        
        logging.info("Preloaded common airport and airline data")

# Global cache instance
cache = AirportAirlineCache()

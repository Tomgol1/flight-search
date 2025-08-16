import json
import os
import logging
from datetime import datetime, timedelta

class AirportAirlineCache:
    def __init__(self, cache_file="airport_airline_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """Load cache from file or create new cache"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    # Check if cache is old format, migrate if needed
                    if 'airlines' not in cache_data or 'airports' not in cache_data:
                        return {'airlines': {}, 'airports': {}, 'last_updated': datetime.now().isoformat()}
                    return cache_data
            except Exception as e:
                logging.warning(f"Could not load cache file: {e}. Creating new cache.")
                return {'airlines': {}, 'airports': {}, 'last_updated': datetime.now().isoformat()}
        else:
            return {'airlines': {}, 'airports': {}, 'last_updated': datetime.now().isoformat()}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            self.cache['last_updated'] = datetime.now().isoformat()
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            logging.debug(f"Cache saved to {self.cache_file}")
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
                    logging.debug(f"Cached airline {carrier_code}: {airline_name}")
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
                            logging.debug(f"Cached airport {airport_code}: {airport_name}")
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
            'FI': 'Icelandair', '6H': 'Israir Airlines', 'UP': 'Bahamasair'
        }
        name = airline_names.get(carrier_code, carrier_code)
        # Cache the fallback result too
        self.cache['airlines'][carrier_code] = name
        self._save_cache()
        return name
    
    def _get_airport_fallback(self, airport_code):
        """Static airport mapping as fallback"""
        airport_names = {
            'TLV': 'Ben Gurion Airport, Tel Aviv', 'KEF': 'Keflavik International Airport, Reykjavik',
            'LHR': 'Heathrow Airport, London', 'CDG': 'Charles de Gaulle Airport, Paris',
            'FRA': 'Frankfurt Airport', 'AMS': 'Amsterdam Schiphol Airport',
            'IST': 'Istanbul Airport', 'DXB': 'Dubai International Airport',
            'DOH': 'Hamad International Airport, Doha', 'VIE': 'Vienna International Airport',
            'ZUR': 'Zurich Airport', 'BRU': 'Brussels Airport', 'HEL': 'Helsinki Airport',
            'ARN': 'Stockholm Arlanda Airport', 'MAD': 'Madrid-Barajas Airport',
            'BCN': 'Barcelona Airport', 'LIS': 'Lisbon Airport',
            'JFK': 'John F. Kennedy International Airport, New York',
            'LAX': 'Los Angeles International Airport',
            'ORD': 'O\'Hare International Airport, Chicago'
        }
        name = airport_names.get(airport_code, f"{airport_code} Airport")
        # Cache the fallback result too
        self.cache['airports'][airport_code] = name
        self._save_cache()
        return name
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return {
            'airlines_cached': len(self.cache['airlines']),
            'airports_cached': len(self.cache['airports']),
            'last_updated': self.cache['last_updated']
        }

# Global cache instance
cache = AirportAirlineCache()

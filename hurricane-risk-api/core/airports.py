"""Airport configuration for Hurricane Risk API"""

# Major airports in Atlantic region with daily passenger estimates (2023 data)
MAJOR_AIRPORTS = {
    # US East Coast
    'ATL': {'lat': 33.6407, 'lon': -84.4277, 'daily_passengers': 100000, 'name': 'Hartsfield-Jackson Atlanta'},
    'MIA': {'lat': 25.7959, 'lon': -80.2870, 'daily_passengers': 50000, 'name': 'Miami International'},
    'JFK': {'lat': 40.6413, 'lon': -73.7781, 'daily_passengers': 80000, 'name': 'John F. Kennedy International'},
    'LGA': {'lat': 40.7769, 'lon': -73.8740, 'daily_passengers': 40000, 'name': 'LaGuardia'},
    'BOS': {'lat': 42.3656, 'lon': -71.0096, 'daily_passengers': 30000, 'name': 'Logan International'},
    'DCA': {'lat': 38.8512, 'lon': -77.0402, 'daily_passengers': 25000, 'name': 'Ronald Reagan Washington'},
    'IAD': {'lat': 38.9531, 'lon': -77.4565, 'daily_passengers': 20000, 'name': 'Dulles International'},
    'PHL': {'lat': 39.8729, 'lon': -75.2437, 'daily_passengers': 25000, 'name': 'Philadelphia International'},
    'BWI': {'lat': 39.1774, 'lon': -76.6684, 'daily_passengers': 15000, 'name': 'Baltimore-Washington International'},
    'CLT': {'lat': 35.2144, 'lon': -80.9473, 'daily_passengers': 45000, 'name': 'Charlotte Douglas International'},
    'RDU': {'lat': 35.8776, 'lon': -78.7875, 'daily_passengers': 12000, 'name': 'Raleigh-Durham International'},
    'ORF': {'lat': 36.8945, 'lon': -76.2019, 'daily_passengers': 8000, 'name': 'Norfolk International'},
    'RIC': {'lat': 37.5052, 'lon': -77.3197, 'daily_passengers': 6000, 'name': 'Richmond International'},
    'SAV': {'lat': 32.1276, 'lon': -81.2021, 'daily_passengers': 4000, 'name': 'Savannah/Hilton Head International'},
    'CHS': {'lat': 32.8986, 'lon': -80.0405, 'daily_passengers': 3000, 'name': 'Charleston International'},
    'MYR': {'lat': 33.6797, 'lon': -78.9283, 'daily_passengers': 2000, 'name': 'Myrtle Beach International'},
    # Florida
    'MCO': {'lat': 28.4312, 'lon': -81.3081, 'daily_passengers': 60000, 'name': 'Orlando International'},
    'FLL': {'lat': 26.0716, 'lon': -80.1526, 'daily_passengers': 35000, 'name': 'Fort Lauderdale-Hollywood International'},
    'TPA': {'lat': 27.9755, 'lon': -82.5332, 'daily_passengers': 25000, 'name': 'Tampa International'},
    'RSW': {'lat': 26.5362, 'lon': -81.7552, 'daily_passengers': 8000, 'name': 'Southwest Florida International'},
    'PBI': {'lat': 26.6832, 'lon': -80.0956, 'daily_passengers': 12000, 'name': 'Palm Beach International'},
    'JAX': {'lat': 30.4941, 'lon': -81.6879, 'daily_passengers': 8000, 'name': 'Jacksonville International'},
    'EYW': {'lat': 24.5561, 'lon': -81.7596, 'daily_passengers': 1000, 'name': 'Key West International'},
    # Caribbean
    'SJU': {'lat': 18.4394, 'lon': -66.0018, 'daily_passengers': 15000, 'name': 'Luis Muñoz Marín International'},
    'AUA': {'lat': 12.5014, 'lon': -70.0152, 'daily_passengers': 3000, 'name': 'Queen Beatrix International'},
    'BGI': {'lat': 13.0746, 'lon': -59.4925, 'daily_passengers': 2000, 'name': 'Grantley Adams International'},
    'SXM': {'lat': 18.0409, 'lon': -63.1089, 'daily_passengers': 1500, 'name': 'Princess Juliana International'},
    'NAS': {'lat': 25.0389, 'lon': -77.4662, 'daily_passengers': 2000, 'name': 'Lynden Pindling International'},
    'PLS': {'lat': 21.7736, 'lon': -72.2659, 'daily_passengers': 1000, 'name': 'Providenciales International'},
    # Bermuda
    'BDA': {'lat': 32.3640, 'lon': -64.6787, 'daily_passengers': 1500, 'name': 'L.F. Wade International'},
    # Central America
    'PTY': {'lat': 9.0714, 'lon': -79.3835, 'daily_passengers': 8000, 'name': 'Tocumen International'},
    'SJO': {'lat': 9.9939, 'lon': -84.2089, 'daily_passengers': 5000, 'name': 'Juan Santamaría International'},
}

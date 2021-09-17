PROJECTED_CRS_SRID = 2154
WAYPOINT_MOTORWAY_DISTANCE_THRESHOLD = 1  # Maximum distance to attach a motorway element to the route in meter

# Default fuel consumptions in l/100km
CONSUMPTION_REDUCTION_FACTOR_110_130 = 0.25
DEFAULT_NON_MOTORWAY_CONSUMPTION = 6
DEFAULT_MOTORWAY_130KMH_CONSUMPTION = 6
DEFAULT_MOTORWAY_110KMH_CONSUMPTION = (1 - CONSUMPTION_REDUCTION_FACTOR_110_130) * DEFAULT_MOTORWAY_130KMH_CONSUMPTION

# Consumption bounds for data validation (in l/100km)
MINIMUM_CONSUMPTION = 1
MAXIMUM_CONSUMPTION = 30

VEHICLE_TYPES = ['Moto', 'Compacte', 'Citadine', 'Berline', 'SUV', 'Familiale']
FUEL_TYPES = ['Diesel', 'Essence']
# kg of CO2 emitted per liter of fuel
# source: https://www.bilans-ges.ademe.fr/documentation/UPLOAD_DOC_FR/index.htm?new_liquides.htm
FUEL_CO2_EMISSIONS = {
    'Diesel': 3.10,
    'Essence': 2.75
}

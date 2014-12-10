
# import here to avoid circular imports
from . import providers


# provide single instance and API
from .providerbase import PoiLookupService

poi_service = PoiLookupService()

get_categories = poi_service.get_categories
by_id = poi_service.by_id
get_points_for_categories = poi_service.get_points_for_categories
set_config_path = poi_service.set_config_path

"""
Best Buy API Client
Migrated from Android App's BestBuyApiService.kt and RetrofitClient.kt
"""
import httpx
import re
from typing import Optional, List, Dict, Any
from app.config import settings
from app.schemas.product import Product, ProductSearchResponse
from app.schemas.store import Store, StoreAvailability, StoreSearchResponse
from app.schemas.category import Category, CategorySearchResponse
from app.services.rate_limiter import RateLimiter
import logging
import urllib.parse

logger = logging.getLogger(__name__)

# Common category cache (reduces API calls for frequently used categories)
# Sourced from Best Buy official app category taxonomy (2026)
COMMON_CATEGORIES = {
    # ── Computers ─────────────────────────────────────────────────────────────
    "laptops": "abcat0502000",
    "laptop": "abcat0502000",
    "all_laptops": "pcmcat138500050001",
    "notebooks": "abcat0502000",
    "desktops": "abcat0501000",
    "desktop": "abcat0501000",
    "all_desktops": "pcmcat143400050013",
    "gaming_desktops": "abcat0501002",
    "gaming desktop": "abcat0501002",
    "macbooks": "abcat0502000",  # Laptops category, filter by manufacturer=Apple
    "mac_mini": "abcat0501000",
    "imac": "abcat0501000",
    "mac_pro": "abcat0501000",
    "mac_studio": "abcat0501000",
    "monitors": "abcat0513000",
    "monitor": "abcat0513000",
    "tablets": "abcat0503000",
    "tablet": "abcat0503000",
    "ipads": "abcat0503000",
    "ipad": "abcat0503000",
    "computer_accessories": "pcmcat209000050006",
    # ── Mobile ────────────────────────────────────────────────────────────────
    "cell_phones": "abcat0800000",
    "phones": "abcat0800000",
    "phone": "abcat0800000",
    "smartphones": "abcat0800000",
    "unlocked_phones": "abcat0800000",
    "iphones": "abcat0800000",
    "samsung_phones": "abcat0800000",
    "cell_phone_cases": "pcmcat312100050015",
    "cell_phone_chargers": "pcmcat209000050006",
    # ── TVs / Audio / Video ───────────────────────────────────────────────────
    "tvs": "abcat0101000",
    "tv": "abcat0101000",
    "televisions": "abcat0101000",
    "flat_screen_tvs": "abcat0101000",
    "projectors": "abcat0102000",
    "streaming_media": "pcmcat241600050001",
    "streaming": "pcmcat241600050001",
    "tv_accessories": "abcat0107000",
    "sound_bars": "abcat0204013",
    "soundbar": "abcat0204013",
    "soundbars": "abcat0204013",
    "receivers": "abcat0204001",
    "amplifiers": "abcat0204001",
    "speakers": "abcat0204009",
    "speaker": "abcat0204009",
    "headphones": "abcat0204000",
    "headphone": "abcat0204000",
    "earbuds": "abcat0204000",
    # ── Cameras / Imaging ─────────────────────────────────────────────────────
    "cameras": "abcat0400000",
    "camera": "abcat0400000",
    "digital_cameras": "abcat0400000",
    "dslr": "abcat0401000",
    "dslr_cameras": "abcat0401000",
    "mirrorless": "abcat0401001",
    "mirrorless_cameras": "abcat0401001",
    "point_shoot": "abcat0401002",
    "point_and_shoot": "abcat0401002",
    "camera_accessories": "pcmcat232400050000",
    "drones": "pcmcat331600050018",
    "drone": "pcmcat331600050018",
    "security_cameras": "pcmcat190100050002",
    "security_camera": "pcmcat190100050002",
    # ── Major Appliances ──────────────────────────────────────────────────────
    "refrigerator": "abcat0912000",
    "refrigerators": "abcat0912000",
    "fridge": "abcat0912000",
    "french_door_fridge": "abcat0912000",
    "side_by_side_fridge": "abcat0912000",
    "dishwasher": "abcat0902000",
    "dishwashers": "abcat0902000",
    "range": "abcat0906000",
    "ranges": "abcat0906000",
    "oven": "abcat0906000",
    "ovens": "abcat0906000",
    "cooktop": "abcat0909000",
    "cooktops": "abcat0909000",
    "microwave": "abcat0905000",
    "microwaves": "abcat0905000",
    "washer": "abcat0901000",
    "washers": "abcat0901000",
    "dryer": "abcat0901000",
    "dryers": "abcat0901000",
    "washers_dryers": "abcat0901000",
    "freezer": "abcat0910000",
    "freezers": "abcat0910000",
    "ice_maker": "abcat0910000",
    # ── Small Appliances / Home ───────────────────────────────────────────────
    "small_kitchen": "abcat0913000",
    "small_kitchen_appliances": "abcat0913000",
    "vacuum": "abcat0920000",
    "vacuums": "abcat0920000",
    "floor_care": "abcat0920000",
    "air_purifier": "abcat0917000",
    "air_purifiers": "abcat0917000",
    "space_heater": "abcat0914000",
    "space_heaters": "abcat0914000",
    "humidifier": "abcat0919000",
    "humidifiers": "abcat0919000",
    "air_conditioner": "abcat0907004",
    "air_conditioners": "abcat0907004",
    "window_ac": "abcat0907004",
    "portable_ac": "abcat0907004",
    "portable_air_conditioner": "abcat0907004",
    "air_fryer": "abcat0912013",
    "air_fryers": "abcat0912013",
    "grills": "pcmcat196100050008",
    "grill": "pcmcat196100050008",
    # ── Gaming ────────────────────────────────────────────────────────────────
    "gaming": "abcat0700000",
    "game_consoles": "abcat0700000",
    "video_games": "abcat0702000",
    "game_controllers": "abcat0707000",
    "pc_gaming": "pcmcat324700050000",
    "virtual_reality": "pcmcat352800050000",
    "vr": "pcmcat352800050000",
    # ── Smart Home / Networking ───────────────────────────────────────────────
    "smart_home": "pcmcat248700050021",
    "networking": "pcmcat143400050012",
    "wifi": "pcmcat143400050012",
    "router": "pcmcat143400050012",
    "smart_speakers": "pcmcat732900050000",
    "smart_speaker": "pcmcat732900050000",
    "smart_thermostat": "pcmcat302600050001",
    "smart_thermostats": "pcmcat302600050001",
    "smart_lighting": "pcmcat248700050015",
    # ── Printers / Storage ────────────────────────────────────────────────────
    "printers": "abcat0301000",
    "printer": "abcat0301000",
    "storage": "abcat0504000",
    # ── Wearables ─────────────────────────────────────────────────────────────
    "smartwatch": "abcat0812010",
    "smartwatches": "abcat0812010",
    "fitness_tracker": "pcmcat332900050009",
    "fitness_trackers": "pcmcat332900050009",
    # ── Automotive / EV ───────────────────────────────────────────────────────
    "car_electronics": "abcat0600000",
    "car_safety": "abcat0600000",
    "ev_charging": "pcmcat382300050000",
    "electric_scooter": "pcmcat317600050000",
    "electric_scooters": "pcmcat317600050000",
    # ── Health & Personal Care ────────────────────────────────────────────────
    "hair_care": "pcmcat209100050001",
    "shaving": "pcmcat209100050002",
    "oral_care": "pcmcat209100050003",
    # ── Other ─────────────────────────────────────────────────────────────────
    "toys": "pcmcat328600050000",
    "fitness_equipment": "pcmcat309700050018",
    "office_furniture": "pcmcat204400050019",
    "patio": "pcmcat217700050006",
    "tv_stands": "pcmcat152300050004",
    "tablet_accessories": "pcmcat312100050015",
}

# ── Sparky-like complementary category map ────────────────────────────────────
# Maps a product's Browse category ID to complementary search queries.
# Used by get_complementary_products() when alsoBought returns no results.
# search_products() is reliable and does NOT hit mostViewed quota limits.
CATEGORY_COMPLEMENT_MAP: Dict[str, List[str]] = {
    # ── TVs / Audio / Video ───────────────────────────────────────────────────
    # TVs → Sound Bars, Streaming Devices, TV Accessories (mounts, cables)
    "abcat0101000": ["abcat0204013", "pcmcat241600050001", "abcat0107000"],
    # Home Theater Projectors → Sound Bars, Streaming, TV Accessories
    "abcat0102000": ["abcat0204013", "pcmcat241600050001", "abcat0107000"],
    # TV Accessories → TVs, Sound Bars, Streaming Devices
    "abcat0107000": ["abcat0101000", "abcat0204013", "pcmcat241600050001"],
    # Streaming Media → TVs, Sound Bars, TV Accessories
    "pcmcat241600050001": ["abcat0101000", "abcat0204013", "abcat0107000"],
    # Sound Bars → Receivers, TV Accessories, Streaming Devices
    "abcat0204013": ["abcat0204001", "abcat0107000", "pcmcat241600050001"],
    # Receivers & Amplifiers → Speakers, Sound Bars, Cables/Accessories
    "abcat0204001": ["abcat0204009", "abcat0204013", "pcmcat209000050006"],
    # Speakers → Receivers, Sound Bars, Cables/Accessories
    "abcat0204009": ["abcat0204001", "abcat0204013", "pcmcat209000050006"],
    # Headphones / Earbuds → Phone Accessories, Smartwatches, Cables
    "abcat0204000": ["pcmcat209000050006", "abcat0812010", "pcmcat241600050001"],
    # ── Computers ─────────────────────────────────────────────────────────────
    # Laptops → Computer Accessories, External Monitors, Storage
    "abcat0502000": ["pcmcat209000050006", "abcat0513000", "abcat0504000"],
    # All Laptops → Computer Accessories, External Monitors, Storage
    "pcmcat138500050001": ["pcmcat209000050006", "abcat0513000", "abcat0504000"],
    # Desktops → Monitors, Keyboards & Mice, Storage
    "abcat0501000": ["abcat0513000", "pcmcat128500050004", "abcat0504000"],
    # All Desktops → Monitors, Keyboards & Mice, Storage
    "pcmcat143400050013": ["abcat0513000", "pcmcat128500050004", "abcat0504000"],
    # Gaming Desktops → Monitors, Keyboards & Mice, PC Gaming Accessories
    "abcat0501002": ["abcat0513000", "pcmcat128500050004", "pcmcat324700050000"],
    # Monitors → Monitor Arms/Stands (Accessories), Webcams, Storage
    "abcat0513000": ["pcmcat209000050006", "abcat0504000", "pcmcat128500050004"],
    # Tablets → Tablet Cases, Computer Accessories, Storage
    "abcat0503000": ["pcmcat312100050015", "pcmcat209000050006", "abcat0504000"],
    # Computer Accessories → Monitors, Storage, Printers
    "pcmcat209000050006": ["abcat0513000", "abcat0504000", "abcat0301000"],
    # Storage (HDD/SSD/Flash) → Computer Accessories, Laptops, Desktops
    "abcat0504000": ["pcmcat209000050006", "abcat0502000", "abcat0501000"],
    # ── Mobile ────────────────────────────────────────────────────────────────
    # Cell Phones → Phone Cases, Headphones, Chargers/Accessories
    "abcat0800000": ["pcmcat312100050015", "abcat0204000", "pcmcat209000050006"],
    # Cell Phone Cases → Screen Protectors (Accessories), Chargers, Headphones
    "pcmcat312100050015": ["pcmcat209000050006", "abcat0204000", "abcat0800000"],
    # ── Cameras / Imaging ─────────────────────────────────────────────────────
    # Digital Cameras → Lenses/Accessories, Memory Cards/Storage, Bags
    "abcat0400000": ["pcmcat232400050000", "abcat0504000", "pcmcat209000050006"],
    # DSLR Cameras → Lenses/Accessories, Memory Cards/Storage
    "abcat0401000": ["pcmcat232400050000", "abcat0504000"],
    # Mirrorless Cameras → Lenses/Accessories, Memory Cards/Storage
    "abcat0401001": ["pcmcat232400050000", "abcat0504000"],
    # Point & Shoot → Memory Cards/Storage, Camera Accessories
    "abcat0401002": ["abcat0504000", "pcmcat232400050000"],
    # Camera Accessories → Cameras, Storage, Tripods/Bags (Accessories)
    "pcmcat232400050000": ["abcat0400000", "abcat0504000", "pcmcat209000050006"],
    # Drones → Camera Accessories, Storage, Computer Accessories
    "pcmcat331600050018": ["pcmcat232400050000", "abcat0504000", "pcmcat209000050006"],
    # Security Cameras → Networking, Storage, Smart Home
    "pcmcat190100050002": ["pcmcat143400050012", "abcat0504000", "pcmcat248700050021"],
    # ── Gaming ────────────────────────────────────────────────────────────────
    # Gaming Consoles → Video Games, Controllers, Gaming Headsets
    "abcat0700000": ["abcat0702000", "abcat0707000", "abcat0204000"],
    # Video Games → Game Controllers, Gaming Headsets, Gaming Consoles
    "abcat0702000": ["abcat0707000", "abcat0204000", "abcat0700000"],
    # Game Controllers → Video Games, Gaming Headsets, Gaming Consoles
    "abcat0707000": ["abcat0702000", "abcat0204000", "abcat0700000"],
    # PC Gaming → Gaming Monitors, Gaming Keyboards/Mice, Gaming Headsets
    "pcmcat324700050000": ["abcat0513000", "pcmcat128500050004", "abcat0204000"],
    # Virtual Reality → PC Gaming, Gaming Controllers, Headphones
    "pcmcat352800050000": ["pcmcat324700050000", "abcat0707000", "abcat0204000"],
    # ── Major Appliances ──────────────────────────────────────────────────────
    # Refrigerators → Freezers/Ice Makers, Small Kitchen Appliances, Accessories
    "abcat0912000": ["abcat0910000", "abcat0913000", "pcmcat209000050006"],
    # Dishwashers → Small Kitchen Appliances, Accessories
    "abcat0902000": ["abcat0913000", "pcmcat209000050006"],
    # Ranges/Ovens → Small Kitchen Appliances, Cooktops, Accessories
    "abcat0906000": ["abcat0913000", "abcat0909000", "pcmcat209000050006"],
    # Cooktops → Ranges/Ovens, Small Kitchen Appliances, Accessories
    "abcat0909000": ["abcat0906000", "abcat0913000", "pcmcat209000050006"],
    # Microwaves → Small Kitchen Appliances, Ranges/Ovens, Accessories
    "abcat0905000": ["abcat0913000", "abcat0906000", "pcmcat209000050006"],
    # Washers & Dryers → Small Appliances, Accessories
    "abcat0901000": ["pcmcat209000050006", "abcat0913000"],
    # Freezers & Ice Makers → Small Kitchen Appliances, Refrigerators, Accessories
    "abcat0910000": ["abcat0913000", "abcat0912000", "pcmcat209000050006"],
    # ── Small Appliances / Home ───────────────────────────────────────────────
    # Small Kitchen Appliances → Ranges/Ovens, Refrigerators, Accessories
    "abcat0913000": ["abcat0906000", "abcat0912000", "pcmcat209000050006"],
    # Vacuums & Floor Care → Air Purifiers, Small Kitchen Appliances, Accessories
    "abcat0920000": ["abcat0917000", "abcat0913000", "pcmcat209000050006"],
    # Air Purifiers → Humidifiers, Vacuums, Accessories
    "abcat0917000": ["abcat0919000", "abcat0920000", "pcmcat209000050006"],
    # Space Heaters → Humidifiers, Air Purifiers, Accessories
    "abcat0914000": ["abcat0919000", "abcat0917000", "pcmcat209000050006"],
    # Humidifiers → Air Purifiers, Space Heaters, Accessories
    "abcat0919000": ["abcat0917000", "abcat0914000", "pcmcat209000050006"],
    # Air Conditioners → Air Purifiers, Space Heaters, Accessories
    "abcat0907004": ["abcat0917000", "abcat0914000", "pcmcat209000050006"],
    # Grills & Outdoor → Small Kitchen Appliances, Patio, Accessories
    "pcmcat196100050008": ["abcat0913000", "pcmcat217700050006", "pcmcat209000050006"],
    # ── Smart Home / Networking ───────────────────────────────────────────────
    # Smart Home → Smart Speakers, Smart Lighting, Smart Thermostats
    "pcmcat248700050021": ["pcmcat732900050000", "pcmcat248700050015", "pcmcat302600050001"],
    # Smart Speakers & Displays → Smart Home, Smart Lighting, Smart Thermostats
    "pcmcat732900050000": ["pcmcat248700050021", "pcmcat248700050015", "pcmcat302600050001"],
    # Smart Thermostats → Smart Home, Smart Lighting, Networking
    "pcmcat302600050001": ["pcmcat248700050021", "pcmcat248700050015", "pcmcat143400050012"],
    # Smart Lighting → Smart Home, Smart Speakers, Smart Thermostats
    "pcmcat248700050015": ["pcmcat248700050021", "pcmcat732900050000", "pcmcat302600050001"],
    # Wi-Fi & Networking → Smart Home, Computer Accessories, Security Cameras
    "pcmcat143400050012": ["pcmcat248700050021", "pcmcat209000050006", "pcmcat190100050002"],
    # ── Printers / Storage ────────────────────────────────────────────────────
    # Printers → Computer Accessories (ink/toner/paper), Storage, Networking
    "abcat0301000": ["pcmcat209000050006", "abcat0504000", "pcmcat143400050012"],
    # ── Wearables ─────────────────────────────────────────────────────────────
    # Smartwatches → Fitness Trackers, Phone Accessories, Headphones
    "abcat0812010": ["pcmcat332900050009", "pcmcat209000050006", "abcat0204000"],
    # Fitness Trackers → Smartwatches, Fitness Equipment, Headphones
    "pcmcat332900050009": ["abcat0812010", "pcmcat309700050018", "abcat0204000"],
    # ── Automotive / EV ───────────────────────────────────────────────────────
    # Car Electronics → Security Cameras, Networking, Accessories
    "abcat0600000": ["pcmcat190100050002", "pcmcat209000050006", "abcat0504000"],
    # EV Charging → Car Electronics, Smart Home, Accessories
    "pcmcat382300050000": ["abcat0600000", "pcmcat248700050021", "pcmcat209000050006"],
    # Electric Scooters → Car Electronics, Wearables, Accessories
    "pcmcat317600050000": ["abcat0600000", "abcat0812010", "pcmcat209000050006"],
    # ── Other ─────────────────────────────────────────────────────────────────
    # Fitness Equipment → Fitness Trackers, Smartwatches, Headphones
    "pcmcat309700050018": ["pcmcat332900050009", "abcat0812010", "abcat0204000"],
    # Office Furniture → Monitors, Computer Accessories, Printers
    "pcmcat204400050019": ["abcat0513000", "pcmcat209000050006", "abcat0301000"],
    # Patio → Grills, Smart Lighting, Accessories
    "pcmcat217700050006": ["pcmcat196100050008", "pcmcat248700050015", "pcmcat209000050006"],
    # TV Stands → TVs, Sound Bars, TV Accessories
    "pcmcat152300050004": ["abcat0101000", "abcat0204013", "abcat0107000"],
    # Toys → Gaming Consoles, Video Games, Fitness Equipment
    "pcmcat328600050000": ["abcat0700000", "abcat0702000", "pcmcat309700050018"],
    # Tablet Accessories → Tablets, Computer Accessories, Storage
    "pcmcat312100050015": ["abcat0503000", "pcmcat209000050006", "abcat0504000"],
}

# ── Category name → fallback search queries (quota-safe) ─────────────────────
# Keys are lowercase category/product type names as seen in Room DB category strings.
# Used when alsoBought returns 0 results — ONE targeted search_products call.
# Sourced from Best Buy official app category taxonomy (2026)
CATEGORY_NAME_TO_QUERIES: Dict[str, str] = {
    # ── TVs / Displays ────────────────────────────────────────────────────────
    "televisions":                    "soundbar streaming device",
    "tv":                             "soundbar streaming device",
    "television":                     "soundbar streaming device",
    "flat-screen tvs":                "soundbar streaming device",
    "flat screen tvs":                "soundbar streaming device",
    "oled":                           "soundbar HDMI cable",
    "qled":                           "soundbar HDMI cable",
    "4k tv":                          "soundbar streaming device",
    "monitors":                       "monitor stand webcam",
    "monitor":                        "monitor stand webcam",
    "projectors":                     "soundbar projector screen",
    "streaming media players":        "HDMI cable remote streaming",
    "streaming media player":         "HDMI cable remote streaming",
    "tv & home theater accessories":  "HDMI cable TV mount surge protector",
    # ── Audio ─────────────────────────────────────────────────────────────────
    "sound bars":                     "receiver HDMI cable TV wall mount",
    "sound bar":                      "receiver HDMI cable TV wall mount",
    "soundbar":                       "receiver HDMI cable TV wall mount",
    "receivers & amplifiers":         "speaker wire speaker surround sound",
    "speakers":                       "speaker stand audio cable",
    "speaker":                        "speaker stand audio cable",
    "headphones":                     "headphone stand audio cable",
    "headphone":                      "headphone stand audio cable",
    "earbuds":                        "earbuds case wireless charger",
    # ── Computers ─────────────────────────────────────────────────────────────
    "laptops":                        "laptop bag USB hub",
    "laptop":                         "laptop bag USB hub",
    "notebooks":                      "laptop bag external monitor",
    "macbooks":                       "laptop bag USB hub",
    "desktops":                       "monitor keyboard mouse",
    "desktop":                        "monitor keyboard mouse",
    "gaming desktops":                "gaming monitor gaming keyboard gaming headset",
    "tablets":                        "tablet case keyboard",
    "tablet":                         "tablet case keyboard",
    "ipads":                          "iPad case keyboard Apple Pencil",
    "monitors":                       "monitor stand monitor arm webcam",
    "computer accessories & peripherals": "USB hub keyboard mouse monitor",
    "pc gaming":                      "gaming headset gaming mouse gaming keyboard",
    "virtual reality":                "VR controller VR head strap battery",
    # ── Mobile ────────────────────────────────────────────────────────────────
    "cell phones":                    "phone case wireless earbuds wireless charger",
    "cell phone":                     "phone case wireless earbuds wireless charger",
    "smartphones":                    "phone case wireless earbuds wireless charger",
    "unlocked cell phones":           "phone case screen protector wireless charger",
    "iphones":                        "iPhone case AirPods wireless charger",
    "samsung galaxy phones":          "Samsung case Galaxy Buds wireless charger",
    "cell phone cases":               "screen protector wireless charger cable",
    "cell phone chargers & cables":   "wireless charger USB hub power bank",
    "tablet accessories":             "tablet case stylus keyboard",
    # ── Cameras / Imaging ─────────────────────────────────────────────────────
    "cameras":                        "camera memory card camera bag",
    "camera":                         "camera memory card camera bag",
    "digital cameras":                "camera memory card camera bag",
    "mirrorless cameras":             "camera lens memory card camera bag",
    "dslr":                           "camera lens memory card flash",
    "dslr cameras":                   "camera lens memory card flash",
    "point & shoot cameras":          "memory card camera case",
    "digital camera accessories":     "memory card camera bag tripod",
    "drones & drone accessories":     "drone battery propeller drone bag",
    "security cameras & surveillance": "security camera mount NVR Ethernet cable",
    # ── Gaming ────────────────────────────────────────────────────────────────
    "video games":                    "gaming headset game controller charging dock",
    "gaming":                         "gaming headset game controller charging dock",
    "game consoles":                  "gaming headset controller charging dock",
    "playstation":                    "PlayStation controller gaming headset",
    "xbox":                           "Xbox controller gaming headset",
    "nintendo":                       "Nintendo Switch case controller",
    # ── Major Appliances ──────────────────────────────────────────────────────
    "refrigerators":                  "water filter ice maker refrigerator organizer",
    "refrigerator":                   "water filter ice maker refrigerator organizer",
    "fridge":                         "water filter ice maker refrigerator organizer",
    "dishwashers":                    "dishwasher cleaner dishwasher rack",
    "dishwasher":                     "dishwasher cleaner dishwasher rack",
    "ranges":                         "range hood cookware baking sheet",
    "range":                          "range hood cookware baking sheet",
    "cooktops":                       "range hood cookware induction pan",
    "microwaves":                     "microwave tray microwave cleaner plate",
    "microwave":                      "microwave tray microwave cleaner plate",
    "washers & dryers":               "laundry detergent dryer sheet pedestal",
    "washer":                         "laundry detergent dryer sheet",
    "dryer":                          "dryer sheet laundry detergent dryer vent",
    "freezers & ice makers":          "freezer basket ice maker water filter",
    "freezer":                        "freezer basket ice maker water filter",
    # ── Small Appliances / Home ───────────────────────────────────────────────
    "small kitchen appliances":       "coffee maker air fryer blender toaster",
    "vacuums & floor care":           "vacuum filter vacuum bag mop pad",
    "vacuum":                         "vacuum filter vacuum bag mop pad",
    "air purifiers":                  "air purifier filter humidifier",
    "air purifier":                   "air purifier filter",
    "space heaters":                  "space heater thermostat humidifier",
    "humidifiers":                    "humidifier filter air purifier",
    "air conditioners":               "window kit remote control cover",
    "air conditioner":                "window kit remote control cover",
    "window air conditioner":         "window kit remote control cover",
    "portable air conditioner":       "window kit exhaust hose",
    "grills & outdoor kitchens":      "grill cover grill brush outdoor thermometer",
    # ── Smart Home / Networking ───────────────────────────────────────────────
    "smart home":                     "smart plug smart bulb smart hub",
    "smart speakers & displays":      "smart home hub smart bulb smart plug",
    "smart thermostats":              "smart thermostat sensor smart home hub",
    "smart lighting":                 "smart bulb smart switch smart home hub",
    "wi-fi & networking":             "WiFi extender Ethernet switch access point",
    "networking":                     "WiFi extender Ethernet switch access point",
    # ── Printers ─────────────────────────────────────────────────────────────
    "printers":                       "printer ink cartridge paper",
    "printer":                        "printer ink cartridge paper",
    # ── Wearables ────────────────────────────────────────────────────────────
    "smartwatches":                   "smartwatch band wireless charger",
    "smartwatch":                     "smartwatch band wireless charger",
    "fitness trackers & accessories": "fitness band heart rate monitor sports earbuds",
    "fitness tracker":                "fitness band heart rate monitor",
    # ── Automotive / EV ──────────────────────────────────────────────────────
    "car safety & security":          "dash cam backup camera radar detector",
    "ev charging":                    "EV charger charging cable adapter",
    "electric scooters":              "scooter lock helmet scooter bag",
    # ── Health & Personal Care ────────────────────────────────────────────────
    "hair care":                      "hair dryer hair straightener brush",
    "shaving & hair removal":         "razor blade shaving cream trimmer",
    "oral care":                      "electric toothbrush replacement head floss",
    # ── Other ─────────────────────────────────────────────────────────────────
    "toys, games & collectibles":     "board game LEGO trading card",
    "exercise & fitness equipment":   "resistance band yoga mat dumbbells",
    "workout recovery":               "foam roller massage gun heating pad",
    "patio furniture & decor":        "patio cover outdoor cushion string light",
    "office furniture":               "monitor arm desk organizer ergonomic chair",
    "baby care":                      "baby monitor baby cam white noise machine",
    "tv stands":                      "TV mount HDMI cable cable management",
}

def _get_complement_query(category_hints: list, manufacturer_hint: str = None) -> str:
    """
    Derive a single targeted search query from category/manufacturer hints — NO API call needed.
    Returns the first match found in CATEGORY_NAME_TO_QUERIES.
    Manufacturer hint is NOT appended to avoid pulling unrelated brand products.
    """
    for cat in category_hints:
        key = cat.lower().strip()
        if key in CATEGORY_NAME_TO_QUERIES:
            return CATEGORY_NAME_TO_QUERIES[key]
    # Keyword scan as last resort
    cat_str = " ".join(category_hints).lower()
    for keyword, query in [
        ("refrigerator", "water filter ice maker refrigerator organizer"),
        ("fridge", "water filter ice maker refrigerator organizer"),
        ("washer", "laundry detergent dryer sheet"),
        ("dryer", "dryer sheet laundry detergent"),
        ("dishwasher", "dishwasher cleaner dishwasher rack"),
        ("microwave", "microwave tray plate cleaner"),
        ("range", "range hood cookware"),
        ("freezer", "freezer basket ice maker"),
        ("vacuum", "vacuum filter vacuum bag"),
        ("appliance", "kitchen appliance organizer"),
        ("tv", "soundbar streaming device"), ("television", "soundbar streaming device"),
        ("laptop", "laptop bag USB hub"), ("phone", "phone case wireless earbuds"),
        ("camera", "camera memory card camera bag"), ("game", "gaming headset controller"),
        ("tablet", "tablet case keyboard"), ("smartwatch", "smartwatch band charger"),
        ("speaker", "speaker stand audio cable"), ("printer", "printer ink cartridge"),
        ("drone", "drone battery propeller"), ("smart", "smart home hub smart plug"),
        ("grill", "grill cover grill brush"), ("fitness", "resistance band yoga mat"),
        ("scooter", "scooter lock helmet"), ("ev", "EV charger charging cable"),
    ]:
        if keyword in cat_str:
            return query
    return ""  # give up — no fallback query available


class BestBuyAPIClient:
    """
    Best Buy API Client
    Provides methods to interact with Best Buy Developer API
    """
    
    def __init__(self):
        self.base_url = settings.bestbuy_api_base_url
        self.api_key = settings.bestbuy_api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Initialize rate limiter (5 req/min, 50,000 req/day — free developer tier)
        self.rate_limiter = RateLimiter(
            requests_per_minute=5,
            requests_per_day=50000
        )
        
        # Category cache to reduce API calls
        self._category_cache: Dict[str, Category] = {}  # category_id -> Category
        self._search_cache: Dict[str, CategorySearchResponse] = {}  # search_name -> response
        self._category_cache_initialized = False
        
        logger.info(f"Initialized Best Buy API Client with base URL: {self.base_url}")
        logger.info("Rate limiting enabled: 5 req/min, 50,000 req/day")
        logger.info(f"Common category cache loaded: {len(COMMON_CATEGORIES)} categories")
    
    async def search_by_upc(self, upc: str) -> Optional[Product]:
        """
        Search product by UPC barcode
        Mirrors BestBuyApiService.searchProductByUPC()
        
        Args:
            upc: Product UPC barcode
            
        Returns:
            Product if found, None otherwise
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            url = f"{self.base_url}/v1/products(upc={upc})"
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "show": "sku,name,regularPrice,salePrice,onSale,image,largeFrontImage,mediumImage,thumbnailImage,longDescription,shortDescription,manufacturer,modelNumber,upc,url,addToCartUrl,customerReviewAverage,customerReviewCount,customerTopRated,freeShipping,inStoreAvailability,onlineAvailability,depth,height,width,weight,color,condition,preowned,dollarSavings,percentSavings"
            }
            
            logger.info(f"Searching product by UPC: {upc}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("total", 0) > 0:
                product = Product.model_validate(data["products"][0])
                logger.info(f"Found product: {product.name} (SKU: {product.sku})")
                return product
            
            logger.warning(f"No product found for UPC: {upc}")
            return None
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error searching by UPC {upc}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching by UPC {upc}: {e}")
            raise
    
    async def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """
        Get product by SKU
        Mirrors BestBuyApiService.getProductBySKU()
        
        Uses the filter-style URL /v1/products(sku=XXXXXXX) which is the only
        format confirmed to work with the Best Buy API.
        Nested show fields (accessories.sku etc.) are NOT supported by this
        endpoint and will cause HTTP 400 — only flat fields are requested.
        
        Args:
            sku: Product SKU
            
        Returns:
            Product if found, None otherwise
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()

            # ✅ Correct URL format: /v1/products(sku=XXXXXXX)
            # ❌ Wrong format:       /v1/products/XXXXXXX.json  → HTTP 400
            url = f"{self.base_url}/v1/products(sku={sku})"
            params = {
                "apiKey": self.api_key,
                "format": "json",
                # Note: dot-notation fields like details.name,details.value work on filter endpoints
                "show": (
                    "sku,name,regularPrice,salePrice,onSale,image,mediumImage,"
                    "thumbnailImage,manufacturer,modelNumber,upc,url,"
                    "customerReviewAverage,customerReviewCount,customerTopRated,"
                    "freeShipping,inStoreAvailability,onlineAvailability,"
                    "depth,height,width,weight,color,condition,preowned,"
                    "dollarSavings,percentSavings,warrantyLabor,warrantyParts,"
                    "details.name,details.value"
                )
            }
            
            logger.info(f"Getting product by SKU: {sku}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            # Filter-style endpoint returns a products array
            products_list = data.get("products", [])
            if not products_list:
                logger.warning(f"Product not found for SKU: {sku}")
                return None
            product = Product.model_validate(products_list[0])
            logger.info(f"Found product: {product.name}")
            return product
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Product not found for SKU: {sku}")
                return None
            logger.error(f"HTTP error getting product by SKU {sku}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting product by SKU {sku}: {e}")
            raise
    
    async def search_products(
        self, 
        query: str, 
        page_size: int = 10,
        sort: Optional[str] = None
    ) -> ProductSearchResponse:
        """
        Search products by keyword with intelligent filtering
        Mirrors BestBuyApiService.searchProducts()
        
        Args:
            query: Search keyword with specifications
            page_size: Number of results (max 100)
            sort: Sort order (e.g., "name.asc", "salePrice.desc")
            
        Returns:
            ProductSearchResponse with filtered and ranked products
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Best Buy API uses "products(search=query)" format
            # We need to URL encode the query (e.g., "mac mini" -> "mac%20mini")
            encoded_query = urllib.parse.quote(query)
            url = f"{self.base_url}/v1/products(search={encoded_query})"
            
            # Request more results for better filtering (but limit to conserve API quota)
            # For device searches, we need more results because gift cards/warranties appear first
            request_size = min(page_size * 4, 50)  # Request 4x to filter down, max 50
            
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "show": "sku,name,regularPrice,salePrice,onSale,image,mediumImage,thumbnailImage,shortDescription,manufacturer,modelNumber,upc,url,customerReviewAverage,customerReviewCount,customerTopRated,freeShipping,inStoreAvailability,onlineAvailability,depth,height,width,weight,color,condition,preowned,dollarSavings,percentSavings",
                "pageSize": request_size,
            }
            
            # Use best-selling rank for device/appliance searches to prioritize actual products over accessories
            # For other searches, use name sorting for consistency
            device_keywords = [
                # Electronics
                'iphone', 'ipad', 'macbook', 'laptop', 'phone', 'tablet', 'watch', 'airpods', 'mac mini', 'imac',
                'tv', 'television', 'monitor', 'camera', 'drone', 'speaker', 'soundbar', 'sound bar',
                'printer', 'smartwatch', 'vacuum', 'grill',
                # Major Appliances
                'refrigerator', 'fridge', 'dishwasher', 'washer', 'dryer', 'microwave',
                'range', 'oven', 'cooktop', 'freezer', 'ice maker',
                'air conditioner', 'air conditioning', 'window ac', 'portable ac',
                'window air conditioner', 'portable air conditioner', 'mini split',
                'air fryer', 'air fry',
                # Gaming Consoles (hardware searches — not game title searches)
                'playstation', 'ps5', 'ps4', 'xbox', 'nintendo switch',
            ]
            is_device_search = any(keyword in query.lower() for keyword in device_keywords)
            
            if sort:
                params["sort"] = sort
            elif is_device_search:
                params["sort"] = "bestSellingRank.asc"  # Best sellers first - real products, not gift cards
                logger.info(f"Device search detected, using bestSellingRank.asc sorting")
            else:
                params["sort"] = "name.asc"  # Name sorting for non-device searches
            
            logger.info(f"Searching products with query: {query}")
            logger.debug(f"Request URL: {url}")
            logger.debug(f"Request Params: {params}")
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            # Parse response and handle missing pagination fields
            data = response.json()
            total = data.get("total", 0)
            products = [Product.model_validate(p) for p in data.get("products", [])]
            
            # Best Buy API may not return pagination fields with products(search=...) format
            # Provide sensible defaults
            result = ProductSearchResponse(
                total=total,
                products=products,
                from_=data.get("from", 1),
                to=data.get("to", min(request_size, len(products))),
                current_page=data.get("currentPage", 1),
                total_pages=data.get("totalPages", (total + request_size - 1) // request_size if request_size > 0 else 1)
            )
            
            logger.info(f"Found {result.total} products for query: {query}")
            
            # Apply intelligent filtering and ranking
            result = self._filter_and_rank_results(query, result, page_size)
            
            logger.info(f"After filtering: {len(result.products)} products")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error searching products with query '{query}': {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching products with query '{query}': {e}")
            raise
    
    def _filter_and_rank_results(self, query: str, result: ProductSearchResponse, max_results: int) -> ProductSearchResponse:
        """
        Filter and rank search results based on query relevance
        
        Args:
            query: Original search query
            result: Initial search results
            max_results: Maximum number of results to return
            
        Returns:
            Filtered and ranked ProductSearchResponse
        """
        if not result.products:
            return result
        
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        # Extract product type from query for type matching
        product_type_keywords = {
            # ── Electronics ───────────────────────────────────────────────────
            'iphone': ['iphone'],
            'ipad': ['ipad'],
            'macbook': ['macbook'],
            'imac': ['imac'],
            'mac mini': ['mac mini'],
            'mac pro': ['mac pro'],
            'mac studio': ['mac studio'],
            'airpods': ['airpods', 'air pods'],
            'watch': ['watch', 'apple watch'],
            'laptop': ['laptop', 'notebook'],
            'phone': ['phone', 'smartphone'],
            'tablet': ['tablet'],
            'headphones': ['headphones', 'earbuds', 'earphones'],
            'tv': ['tv ', 'television', 'oled tv', 'qled tv', 'smart tv', 'flat screen tv', '4k tv', 'mini led tv'],
            'monitor': ['monitor', 'computer monitor', 'gaming monitor', 'curved monitor'],
            'camera': ['camera', 'digital camera', 'dslr', 'mirrorless', 'point-and-shoot', 'point and shoot'],
            'drone': ['drone', 'quadcopter', 'unmanned aerial'],
            'speaker': ['speaker', 'bluetooth speaker', 'portable speaker', 'bookshelf speaker', 'home theater speaker'],
            'soundbar': ['soundbar', 'sound bar'],
            'printer': ['printer', 'inkjet printer', 'laser printer', 'all-in-one printer'],
            'smartwatch': ['smartwatch', 'smart watch', 'apple watch', 'galaxy watch', 'garmin watch'],
            # ── Gaming Consoles (platform-specific, must come BEFORE generic 'gaming') ──
            # These are console HARDWARE searches. Game titles follow "Title - Platform" pattern
            # and are filtered out below. Splitting from generic 'gaming' prevents game titles
            # from getting +200 type-match bonus when user searches for the console itself.
            'playstation':     ['playstation 5', 'playstation 4', 'ps5', 'ps4'],
            'xbox':            ['xbox series x', 'xbox series s', 'xbox one x', 'xbox one s', 'xbox one', 'xbox'],
            'nintendo_switch': ['nintendo switch 2', 'nintendo switch oled', 'nintendo switch lite', 'nintendo switch'],
            'gaming': ['game console', 'gaming console', 'game controller'],  # generic fallback only
            # ── Small Appliances / Home ───────────────────────────────────────
            'vacuum': ['vacuum', 'vacuum cleaner', 'robot vacuum', 'canister vacuum', 'stick vacuum', 'cordless vacuum'],
            'air_purifier': ['air purifier', 'air cleaner', 'hepa purifier'],
            'air_conditioner': ['air conditioner', 'window air conditioner', 'portable air conditioner',
                                'window ac', 'portable ac', 'mini split', 'ac unit', 'air conditioning unit'],
            'air_fryer': ['air fryer', 'air fry', 'airfryer'],
            'grill': ['grill', 'bbq', 'gas grill', 'charcoal grill', 'pellet grill', 'kamado grill', 'outdoor grill'],
            # ── Major Appliances ──────────────────────────────────────────────
            'refrigerator': ['refrigerator', 'french door', 'side-by-side', 'bottom freezer', 'top freezer', 'counter-depth', 'counter depth'],
            'fridge': ['refrigerator', 'french door', 'side-by-side'],
            'dishwasher': ['dishwasher'],
            'washer': ['washer', 'washing machine', 'front load', 'top load', 'front-load', 'top-load'],
            'dryer': ['dryer', 'clothes dryer', 'gas dryer', 'electric dryer'],
            'microwave': ['microwave', 'over-the-range', 'countertop microwave', 'built-in microwave'],
            'range': ['range', 'electric range', 'gas range', 'induction range', 'freestanding range', 'slide-in range'],
            'oven': ['oven', 'wall oven', 'double oven', 'single oven'],
            'cooktop': ['cooktop', 'induction cooktop', 'gas cooktop', 'electric cooktop'],
            'freezer': ['freezer', 'chest freezer', 'upright freezer'],
        }

        # Appliance accessory keyword map — products to filter OUT when searching for the appliance itself
        # Key = keyword that must appear in query; Value = name fragments that mark an accessory, not the appliance
        appliance_accessory_filter: dict[str, list[str]] = {
            'refrigerator': ['water filter', 'replacement filter', 'filter for select', 'door panel', 'refrigerator panel',
                             'crisper drawer', 'ice bin', 'drip tray', 'shelf for', 'rack for'],
            'fridge':        ['water filter', 'replacement filter', 'filter for select', 'door panel', 'refrigerator panel'],
            'dishwasher':    ['dishwasher rack', 'dishwasher basket', 'dishwasher cleaner', 'dishwasher detergent'],
            'washer':        ['washer pedestal', 'laundry bag', 'drum cleaner', 'laundry detergent'],
            'dryer':         ['dryer pedestal', 'dryer sheet', 'vent kit', 'drum cleaner'],
            'microwave':     ['turntable plate', 'microwave plate', 'microwave filter', 'grease filter'],
            'range':         ['drip pan', 'range hood', 'burner grate', 'burner knob', 'range knob'],
            'oven':          ['oven rack', 'oven thermometer', 'oven mitt', 'broiler pan'],
            'cooktop':       ['cooktop cleaner', 'induction cookware'],
            'freezer':       ['freezer basket', 'freezer shelf'],
            # ── Small Appliances / Home ───────────────────────────────────────
            'vacuum':        ['vacuum bag', 'replacement filter for', 'brush roll for', 'dustbin for', 'filter pack for', 'vacuum belt'],
            'grill':         ['grill cover', 'grill brush', 'grill mat', 'grill cleaner', 'grill light', 'drip tray for'],
        }

        # Console hardware search → filter out game titles.
        # Best Buy names game titles as: "GameTitle - PlayStation 5" / "GameTitle - Nintendo Switch 2"
        # Console hardware names never follow this "X - Platform" suffix pattern.
        # Only applied when user is NOT explicitly searching for games.
        console_hardware_types = ('playstation', 'xbox', 'nintendo_switch')
        # Game titles on Best Buy use "GameTitle - Platform" naming convention —
        # the platform name appears as a SUFFIX at the END of the product name.
        # Hardware products like "Sony - PlayStation 5 Console" have the platform
        # in the MIDDLE followed by more words, NOT as a terminal suffix.
        #
        # Use regex anchored near the end of the string to avoid false positives:
        # "Sony - PlayStation VR2 - Multi" → 'Sony -' prefix, not a game title suffix
        # "Spider-Man 2 - PlayStation 5"   → ends with platform suffix → game title ✓
        game_title_suffix_regexes = [
            # Matches platform as terminal suffix, after dash OR comma (multi-platform titles).
            # e.g. "Spider-Man 2 - PlayStation 5", "Days Gone - PlayStation 5, PlayStation 4"
            # Hardware like "Sony - PlayStation 5 DualSense - White" ends with "- white" → no match.
            r'[,\-]\s*playstation [45]\s*$',     # "... - PlayStation 5" / "..., PlayStation 4"
            r'[,\-]\s*ps5\s*$',                   # "... - PS5" / "..., PS5"
            r'[,\-]\s*ps4\s*$',                   # "... - PS4" / "..., PS4"
            r'[,\-]\s*xbox series [xs]\s*$',      # "... - Xbox Series X/S"
            r'[,\-]\s*xbox one\s*$',              # "... - Xbox One"
            r'[,\-]\s*nintendo switch 2\s*$',     # "... - Nintendo Switch 2"
            r'[,\-]\s*nintendo switch\s*$',       # "... - Nintendo Switch"
            r'[,\-]\s*switch 2?\s*$',             # "... - Switch 2" / "... - Switch"
            r'- windows(?:\s+\[digital\])?\s*$',  # "Title - Windows [Digital]" PC games
        ]
        # Name-prefix patterns: always indicate non-hardware (PC-branded Sony games)
        game_title_name_prefixes = [
            'playstation pc ',             # "PlayStation PC GameTitle" — Sony PC game branding
        ]
        # Name-suffix patterns: product name ends with this
        game_title_name_endings = [
            '[digital]',                   # "Title [Digital]" — digital download only
        ]
        is_explicit_game_search = any(
            g in query_lower for g in ['game', 'games', 'dlc', 'expansion', 'edition of']
        )
        
        # Detect product type from query
        detected_product_type = None
        for product_type, keywords in product_type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_product_type = product_type
                logger.info(f"Detected product type from query: {product_type}")
                break
        
        # Extract potential specs from query (storage sizes, colors, etc.)
        specs = []
        for term in query_terms:
            # Storage sizes: 64GB, 128GB, 256GB, 512GB, 1TB, 2TB, etc.
            if 'gb' in term.lower() or 'tb' in term.lower():
                specs.append(term)
            # Colors: black, white, silver, gold, etc.
            elif term.lower() in ['black', 'white', 'silver', 'gold', 'blue', 'red', 'green', 'purple', 'pink', 'yellow']:
                specs.append(term)
        
        logger.info(f"Extracted specs from query '{query}': {specs}")
        
        # Define irrelevant product types to filter out
        # Use word boundaries to avoid false positives (e.g., "gift" matching "gifted")
        irrelevant_keywords = [
            'gift card', 'giftcard', 'e-gift', 'egift', 'gift cards',
            'warranty', 'protection plan', 'geek squad',
            'membership', 'subscription', 
            'installation service', 'setup service', 'tech support',
            'applecare', 'apple care'
        ]
        
        def is_irrelevant_product(product_text: str, product_name: str = "") -> tuple[bool, str]:
            """
            Check if product is an irrelevant type (gift card, warranty, service)
            Uses more precise matching to avoid false positives
            Returns: (is_irrelevant, matched_keyword)
            """
            product_lower = product_text.lower()
            
            # Check for exact phrase matches
            for keyword in irrelevant_keywords:
                # Use word boundaries for single words, exact match for phrases
                if ' ' in keyword:  # Multi-word phrase
                    if keyword in product_lower:
                        logger.info(f"  🔍 Matched keyword '{keyword}' (phrase) in: {product_name[:70]}")
                        return True, keyword
                else:  # Single word - check with word boundaries
                    # Check if keyword appears as a standalone word
                    if re.search(r'\b' + re.escape(keyword) + r'\b', product_lower):
                        logger.info(f"  🔍 Matched keyword '{keyword}' (word boundary) in: {product_name[:70]}")
                        return True, keyword
            
            return False, ""
        
        # Score each product
        scored_products = []
        irrelevant_filtered = []  # Track filtered irrelevant products
        
        logger.info(f"Starting product filtering for {len(result.products)} products...")
        
        for product in result.products:
            score = 0
            product_text = f"{product.name} {product.short_description or ''} {product.model_number or ''}".lower()
            
            # FILTER: Skip irrelevant product types (gift cards, warranties, services)
            is_irrelevant, matched_keyword = is_irrelevant_product(product_text, product.name)
            if is_irrelevant:
                logger.info(f"❌ FILTERED (matched '{matched_keyword}'): {product.name[:80]}")
                irrelevant_filtered.append(product.name)
                continue
            else:
                logger.info(f"✅ KEPT (relevant): {product.name[:80]}")
            
            # FILTER: If user is searching for a device/appliance, skip accessories
            # unless the query explicitly mentions accessories
            device_keywords = [
                'iphone', 'ipad', 'macbook', 'laptop', 'phone', 'tablet', 'watch', 'airpods',
                'tv', 'television', 'monitor', 'camera', 'drone', 'speaker', 'soundbar', 'sound bar',
                'printer', 'smartwatch', 'vacuum', 'grill',
                'refrigerator', 'fridge', 'dishwasher', 'washer', 'dryer', 'microwave', 'range', 'oven', 'cooktop', 'freezer',
                'playstation', 'ps5', 'ps4', 'xbox', 'nintendo switch',
            ]
            # NOTE: 'case' intentionally excluded — Apple Watch/iPhone bodies also contain "Aluminum Case"/"Titanium Case"
            # Accessory detection is primarily handled by the is_accessory_by_pattern check below
            accessory_keywords = ['charger', 'cable', 'adapter', 'stand', 'mount', 'screen protector']

            is_device_search = any(device in query_lower for device in device_keywords)
            is_accessory_product = any(accessory in product_text for accessory in accessory_keywords)
            accessory_in_query = any(accessory in query_lower for accessory in accessory_keywords)

            # FILTER: Appliance-specific accessory filtering
            # e.g. searching "refrigerator" → exclude water filters, replacement panels
            is_appliance_accessory = False
            for appliance_kw, accessory_fragments in appliance_accessory_filter.items():
                if appliance_kw in query_lower:
                    product_name_lower_for_acc = product.name.lower()
                    for fragment in accessory_fragments:
                        if fragment in product_name_lower_for_acc:
                            is_appliance_accessory = True
                            logger.info(f"  🔧 Appliance accessory filtered ('{fragment}'): {product.name[:70]}")
                            break
                    if is_appliance_accessory:
                        break
            if is_appliance_accessory:
                continue

            # FILTER: Console hardware search → filter out game titles
            # e.g. "PlayStation 5" search should return consoles, not "HELLDIVERS 2 - PlayStation 5"
            # Uses suffix-anchored regex to avoid false positives on "Sony - PlayStation VR2"
            if detected_product_type in console_hardware_types and not is_explicit_game_search:
                pname_lower = product.name.lower()
                # If the product name contains "console", it IS the console hardware — never filter it.
                is_console_hardware = 'console' in pname_lower
                # Nintendo Switch game titles list MULTIPLE platforms separated by commas
                # e.g. "Luigi's Mansion 2 - Nintendo Switch – OLED, Nintendo Switch, Nintendo Switch Lite"
                # Console hardware (the device itself) only mentions "Nintendo Switch" ONCE.
                is_ns_multi_platform = (
                    not is_console_hardware
                    and detected_product_type == 'nintendo_switch'
                    and pname_lower.count('nintendo switch') >= 2
                )
                is_game_title = (
                    not is_console_hardware
                    and (
                        is_ns_multi_platform
                        or any(pname_lower.startswith(p) for p in game_title_name_prefixes)
                        or any(pname_lower.endswith(e) for e in game_title_name_endings)
                        or any(re.search(pattern, pname_lower) for pattern in game_title_suffix_regexes)
                    )
                )
                if is_game_title:
                    logger.info(f"  🎮 Game title filtered (console hardware search): {product.name[:70]}")
                    continue

            # Additional check: "for <device>" pattern → accessory for the device
            # e.g., "Sport Band for Apple Watch 44mm" when user searches "Apple Watch"
            # Apple Watch DEVICES say "with Sport Band", not "for Apple Watch"
            is_accessory_by_pattern = False
            if detected_product_type and is_device_search and not accessory_in_query:
                type_kws = product_type_keywords.get(detected_product_type, [])
                for type_kw in type_kws:
                    if f"for {type_kw}" in product_text:
                        is_accessory_by_pattern = True
                        logger.info(f"  🔍 Accessory pattern 'for {type_kw}' matched: {product.name[:70]}")
                        break

            if is_device_search and (is_accessory_product or is_accessory_by_pattern) and not accessory_in_query:
                logger.debug(f"Product '{product.name}' is an accessory, but user searched for device, skipping")
                continue
            
            # FILTER: Product type mismatch (e.g., searching "iPhone" but got "iPad")
            if detected_product_type:
                product_name_lower = product.name.lower()
                
                # Define conflicting product types (mutually exclusive)
                conflicts = {
                    # Electronics
                    'iphone': ['ipad', 'ipod', 'macbook', 'imac', 'mac mini', 'mac pro', 'apple watch'],
                    'ipad': ['iphone', 'macbook', 'imac', 'mac mini', 'mac pro'],
                    'macbook': ['iphone', 'ipad', 'imac', 'mac mini', 'mac pro', 'mac studio'],
                    'mac mini': ['iphone', 'ipad', 'macbook', 'imac', 'mac pro', 'mac studio', 'laptop'],
                    'imac': ['iphone', 'ipad', 'macbook', 'mac mini', 'mac pro', 'mac studio', 'laptop'],
                    'mac pro': ['iphone', 'ipad', 'macbook', 'mac mini', 'imac', 'mac studio', 'laptop'],
                    'mac studio': ['iphone', 'ipad', 'macbook', 'mac mini', 'imac', 'mac pro', 'laptop'],
                    'laptop': ['phone', 'tablet', 'watch'],
                    'phone': ['tablet', 'laptop', 'watch', 'ipad'],
                    'tablet': ['phone', 'laptop', 'watch', 'iphone'],
                    # Major Appliances — prevent cross-appliance contamination
                    # ── Electronics ──────────────────────────────────────────
                    'tv':            ['monitor', 'projector', 'computer display'],
                    'monitor':       ['television', 'projector'],
                    'camera':        ['drone', 'webcam', 'security camera'],
                    'drone':         ['security camera', 'webcam'],
                    'vacuum':        ['air purifier', 'humidifier'],
                    # Gaming consoles — prevent cross-platform confusion
                    'playstation':     ['xbox', 'nintendo switch'],
                    'xbox':            ['playstation', 'nintendo switch'],
                    'nintendo_switch': ['playstation', 'xbox'],
                    # ── Major Appliances ─────────────────────────────────────────
                    'refrigerator': ['dishwasher', 'washing machine', 'washer', 'dryer', 'microwave', 'range', 'cooktop', 'freezer'],
                    'fridge':        ['dishwasher', 'washing machine', 'washer', 'dryer', 'microwave', 'range', 'cooktop'],
                    'dishwasher':    ['refrigerator', 'washing machine', 'washer', 'dryer', 'microwave', 'range'],
                    'washer':        ['refrigerator', 'dishwasher', 'dryer', 'microwave', 'range', 'cooktop'],
                    'dryer':         ['refrigerator', 'dishwasher', 'washer', 'microwave', 'range', 'cooktop'],
                    'microwave':     ['refrigerator', 'dishwasher', 'washer', 'dryer', 'range', 'cooktop'],
                    'range':         ['refrigerator', 'dishwasher', 'washer', 'dryer', 'microwave'],
                    'oven':          ['refrigerator', 'dishwasher', 'washer', 'dryer', 'microwave'],
                    'cooktop':       ['refrigerator', 'dishwasher', 'washer', 'dryer', 'microwave'],
                    'freezer':       ['dishwasher', 'washer', 'dryer', 'microwave', 'range', 'cooktop'],
                    # Air conditioner — filter out "air" products that are NOT cooling units
                    'air_conditioner': ['air fryer', 'air fry', 'air purifier', 'dehumidifier',
                                        'humidifier', 'space heater', 'fan ', 'tower fan', 'ceiling fan',
                                        'box fan', 'desk fan', 'standing fan', 'bladeless fan'],
                }
                
                # Check if product name contains conflicting type
                has_conflict = False
                if detected_product_type in conflicts:
                    for conflicting_type in conflicts[detected_product_type]:
                        if conflicting_type in product_name_lower:
                            logger.debug(f"Product '{product.name}' is {conflicting_type}, but user searched for {detected_product_type}, skipping")
                            has_conflict = True
                            break
                
                if has_conflict:
                    continue  # Skip this product entirely
                
                # Check if product matches expected type (bonus points)
                type_keywords = product_type_keywords.get(detected_product_type, [])
                if any(keyword in product_name_lower for keyword in type_keywords):
                    # For console hardware searches: strongly boost products that contain "console"
                    # so hardware outranks game titles that happen to match the platform name.
                    if detected_product_type in console_hardware_types and 'console' in product_name_lower:
                        score += 500  # Console hardware gets highest priority
                        logger.debug(f"Product '{product.name}' is console hardware, +500 score")
                    elif detected_product_type in console_hardware_types:
                        # Platform matched but no "console" keyword → likely a game title; no bonus
                        pass
                    else:
                        score += 200  # Strong bonus for correct product type match
                        logger.debug(f"Product '{product.name}' matches expected type {detected_product_type}, +200 score")
            
            # Exact query match in name (highest priority)
            if query_lower in product.name.lower():
                score += 100
            
            # Check if all specs are present in product text
            specs_matched = 0
            specs_missing = []
            for spec in specs:
                if spec in product_text:
                    specs_matched += 1
                    score += 50  # Bonus for matching spec
                else:
                    specs_missing.append(spec)
            
            # Penalize products missing specs, but don't skip them entirely
            # This allows fallback results when no products match all specs
            if specs and specs_matched < len(specs):
                score -= (len(specs_missing) * 30)  # Penalty for each missing spec
                logger.debug(f"Product '{product.name}' missing specs {specs_missing}, score penalty applied (matched {specs_matched}/{len(specs)})")
            
            # Skip products with very low scores (negative or near-zero)
            if score < 0:
                logger.debug(f"Product '{product.name}' score too low ({score}), skipping")
                continue
            
            # All query terms present (important)
            terms_found = sum(1 for term in query_terms if term in product_text)
            score += terms_found * 10
            
            # Prefer products with model numbers when query has them
            if product.model_number and any(term.replace(' ', '').isalnum() and len(term) > 3 for term in query_terms):
                score += 20
            
            # Availability bonus
            if product.online_availability:
                score += 5
            
            scored_products.append((score, product))
            logger.debug(f"Product '{product.name}' scored: {score}")
        
        # Sort by score (descending) and take top results
        scored_products.sort(key=lambda x: x[0], reverse=True)
        filtered_products = [p for score, p in scored_products[:max_results]]
        
        logger.info(f"Filtered from {len(result.products)} to {len(filtered_products)} products (irrelevant: {len(irrelevant_filtered)}, filtered by score/specs: {len(result.products) - len(irrelevant_filtered) - len(filtered_products)})")
        
        # Log sample of filtered products for debugging
        if not filtered_products and irrelevant_filtered:
            logger.info(f"Sample of irrelevant products filtered: {irrelevant_filtered[:3]}")
        
        # FALLBACK: If filtering removed all products, check if we should return some results
        if not filtered_products and result.products:
            # If MOST products (80%+) are irrelevant types, return empty (truly bad query)
            irrelevant_count = len(irrelevant_filtered)
            irrelevant_ratio = irrelevant_count / len(result.products)

            if irrelevant_ratio >= 0.8:
                logger.warning(f"Most products ({irrelevant_count}/{len(result.products)}, {irrelevant_ratio:.0%}) are irrelevant types. Returning empty results.")
                filtered_products = []
            else:
                # Scoring filtered everything — return top scored products as fallback
                non_irrelevant_count = len(result.products) - irrelevant_count
                if scored_products:
                    logger.warning(f"Score filter removed all {non_irrelevant_count} relevant products. Returning top {max_results} as fallback.")
                    # Re-sort (already sorted) and return top results ignoring score threshold
                    scored_products.sort(key=lambda x: x[0], reverse=True)
                    filtered_products = [p for _, p in scored_products[:max_results]]
                else:
                    logger.info(f"{non_irrelevant_count} products were relevant but all filtered pre-scoring. Returning empty.")
                    filtered_products = []
        
        # Calculate pagination info
        total_filtered = len(filtered_products)
        to_index = min(max_results, total_filtered)
        
        return ProductSearchResponse(
            total=total_filtered,
            products=filtered_products[:max_results],
            from_=1,
            to=to_index,
            current_page=1,
            total_pages=1
        )
    
    @staticmethod
    def _map_recommendation_item(r: dict) -> Product:
        """
        Map a Recommendations API result item (nested structure) to a Product model.
        Recommendations API uses: names.title, prices.current/regular, images.standard,
        customerReviews.averageScore/count, descriptions.short — NOT flat fields.
        """
        current_price = r.get("prices", {}).get("current")
        regular_price = r.get("prices", {}).get("regular")
        on_sale = (
            current_price is not None
            and regular_price is not None
            and current_price < regular_price
        )
        return Product.model_validate({
            "sku": int(r["sku"]) if r.get("sku") else None,
            "name": r.get("names", {}).get("title"),
            "salePrice": current_price,
            "regularPrice": regular_price,
            "onSale": on_sale,
            "image": r.get("images", {}).get("standard"),
            "shortDescription": r.get("descriptions", {}).get("short"),
            "customerReviewAverage": r.get("customerReviews", {}).get("averageScore"),
            "customerReviewCount": r.get("customerReviews", {}).get("count"),
        })

    async def get_recommendations(self, sku: str) -> List[Product]:
        """
        Get product recommendations (Also Viewed)
        Mirrors BestBuyApiService.getRecommendations()
        
        Args:
            sku: Product SKU
            
        Returns:
            List of recommended products
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            url = f"{self.base_url}/v1/products/{sku}/alsoViewed"
            params = {"apiKey": self.api_key}
            
            logger.info(f"Getting recommendations for SKU: {sku}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Recommendations API returns "results" key with nested structure
            products = [self._map_recommendation_item(r) for r in data.get("results", [])]
            logger.info(f"Found {len(products)} recommendations for SKU: {sku}")
            return products
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting recommendations for SKU {sku}: {e}")
            return []  # Return empty list on error
        except Exception as e:
            logger.error(f"Error getting recommendations for SKU {sku}: {e}")
            return []
    
    async def get_similar_products(self, sku: str) -> List[Product]:
        """
        Get similar products
        Mirrors BestBuyApiService.getSimilarProducts()
        
        Args:
            sku: Product SKU
            
        Returns:
            List of similar products
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            url = f"{self.base_url}/beta/products/{sku}/similar"
            params = {"apiKey": self.api_key}
            
            logger.info(f"Getting similar products for SKU: {sku}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Similar endpoint uses same Recommendations API nested structure (results key)
            raw = data.get("results", data.get("products", []))
            products = [self._map_recommendation_item(r) for r in raw]
            logger.info(f"Found {len(products)} similar products for SKU: {sku}")
            return products
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting similar products for SKU {sku}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting similar products for SKU {sku}: {e}")
            return []
    
    async def get_store_availability(
        self,
        sku: str,
        postal_code: Optional[str] = None,
        radius: int = 25,
        max_stores: int = 1,
        product_name: Optional[str] = None
    ) -> StoreSearchResponse:
        """
        Check product availability at nearby Best Buy stores (BOPIS).

        Uses exactly 2 API calls (down from the old 5-call pattern):
          1. GET /v1/stores?area={zip},{radius}&pageSize=1  → nearest store
          2. GET /v1/products/{sku}/stores/{storeId}        → availability at that store

        Args:
            sku: Product SKU
            postal_code: ZIP/Postal code for location (e.g., "94103")
            radius: Search radius in miles (default: 25)
            max_stores: Max stores to check (default: 1 to keep API usage minimal)
            product_name: Optional product name to show in response (skips extra lookup)

        Returns:
            StoreSearchResponse with availability information
        """
        try:
            # ── Step 1: find nearest store(s) ────────────────────────────────
            await self.rate_limiter.acquire()

            store_url = f"{self.base_url}/v1/stores"
            store_params: Dict[str, Any] = {
                "apiKey": self.api_key,
                "format": "json",
                "pageSize": max(1, max_stores),   # at least 1, at most max_stores
                "show": "storeId,storeType,name,address,city,region,postalCode,phone,distance"
            }
            if postal_code:
                store_params["area"] = f"{postal_code},{radius}"
                logger.info(f"Checking store availability for SKU {sku} near {postal_code} (radius: {radius} mi)")
            else:
                logger.info(f"Checking store availability for SKU {sku} (no location filter)")

            store_response = await self.client.get(store_url, params=store_params)
            store_response.raise_for_status()
            stores_data = store_response.json()

            stores_list = stores_data.get("stores", [])
            if not stores_list:
                logger.info(f"No stores found near {postal_code} for SKU {sku}")
                return StoreSearchResponse(
                    sku=int(sku),
                    productName=product_name or f"Product {sku}",
                    stores=[],
                    totalStores=0
                )

            # ── Step 2: check availability at each store (usually just 1) ────
            result_stores: List[StoreAvailability] = []
            for store_info in stores_list[:max(1, max_stores)]:
                try:
                    store = Store(
                        storeId=store_info.get("storeId"),
                        storeType=store_info.get("storeType"),
                        name=store_info.get("name"),
                        address=store_info.get("address"),
                        city=store_info.get("city"),
                        region=store_info.get("region"),
                        postalCode=store_info.get("postalCode"),
                        phone=store_info.get("phone"),
                        distance=store_info.get("distance")
                    )

                    await self.rate_limiter.acquire()
                    avail_url = f"{self.base_url}/v1/products/{sku}/stores/{store.store_id}"
                    avail_response = await self.client.get(
                        avail_url, params={"apiKey": self.api_key}
                    )
                    avail_response.raise_for_status()
                    avail = avail_response.json()

                    result_stores.append(StoreAvailability(
                        store=store,
                        sku=int(sku),
                        inStock=avail.get("inStoreAvailability", False),
                        pickupEligible=avail.get("pickupEligible", False),
                        shipFromStoreEligible=avail.get("shipFromStoreEligible", False)
                    ))
                    logger.debug(
                        f"Store {store.name}: "
                        f"in_stock={avail.get('inStoreAvailability')}, "
                        f"pickup={avail.get('pickupEligible')}"
                    )
                except Exception as e:
                    logger.warning(f"Error checking availability for store {store_info.get('storeId')}: {e}")

            logger.info(f"Found {len(result_stores)} store(s) for SKU {sku} — 2 API calls used")

            return StoreSearchResponse(
                sku=int(sku),
                productName=product_name or f"Product {sku}",
                stores=result_stores,
                totalStores=len(result_stores)
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error checking store availability for SKU {sku}: {e}")
            return StoreSearchResponse(sku=int(sku), productName=product_name or f"Product {sku}", stores=[], totalStores=0)
        except Exception as e:
            logger.error(f"Error checking store availability for SKU {sku}: {e}")
            return StoreSearchResponse(sku=int(sku), productName=product_name or f"Product {sku}", stores=[], totalStores=0)
    
    async def get_also_bought(self, sku: str) -> List[Product]:
        """
        Get products that customers also bought (cross-sell recommendations)
        
        Args:
            sku: Product SKU
            
        Returns:
            List of products frequently bought together
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            url = f"{self.base_url}/v1/products/{sku}/alsoBought"
            params = {"apiKey": self.api_key}
            
            logger.info(f"Getting alsoBought recommendations for SKU: {sku}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Recommendations API returns "results" key with nested structure
            products = [self._map_recommendation_item(r) for r in data.get("results", [])]
            logger.info(f"Found {len(products)} alsoBought products for SKU: {sku}")
            return products
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting alsoBought for SKU {sku}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting alsoBought for SKU {sku}: {e}")
            return []
    
    async def advanced_search(
        self,
        query: str,
        manufacturer: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        on_sale: Optional[bool] = None,
        free_shipping: Optional[bool] = None,
        in_store_pickup: Optional[bool] = None,
        page_size: int = 10,
        sort: Optional[str] = None
    ) -> ProductSearchResponse:
        """
        Advanced product search with multiple filters and operators
        
        Args:
            query: Search query text
            manufacturer: Filter by manufacturer (e.g., "Apple", "Samsung")
            category: Filter by category name (e.g., "Cell Phones", "Laptops", "Tablets")
            min_price: Minimum price filter
            max_price: Maximum price filter
            on_sale: Filter for products on sale
            free_shipping: Filter for free shipping products
            in_store_pickup: Filter for in-store pickup availability
            page_size: Number of results to return
            sort: Sort order (e.g., "name.asc", "salePrice.asc", "regularPrice.desc")
            
        Returns:
            ProductSearchResponse with filtered results
        """
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # NOTE: We do NOT auto-detect categories to avoid incorrect filtering
            # Best Buy's category structure must be queried from Categories API
            # We rely on:
            # 1. Manufacturer filtering (API-level) - highly effective
            # 2. Product type filtering (client-side) - filters gift cards, warranties, wrong device types
            # 3. Spec matching (client-side) - validates storage, colors, etc.
            
            # Build filter query using Best Buy API format
            # Best Buy uses products(filter1=value1&filter2=value2) format
            filters = []
            
            # Manufacturer filter (highest priority for brand-specific searches)
            if manufacturer:
                filters.append(f"manufacturer={urllib.parse.quote(manufacturer)}")
            
            # Category filter (only if explicitly provided by user)
            # Note: Common categories are cached in COMMON_CATEGORIES dict
            # To get valid categories, query Best Buy Categories API:
            # GET https://api.bestbuy.com/v1/categories?apiKey=KEY
            # Use categoryPath.id (e.g., abcat0400000) or categoryPath.name
            # 
            # Common category IDs:
            # - abcat0502000: Laptops
            # - abcat0501000: Desktops
            # - abcat0800000: Cell Phones
            if category:
                # Prefer categoryPath.id if available, otherwise use categoryPath.name
                # Best Buy uses two ID prefixes: 'abcat' and 'pcmcat'
                if category.startswith('abcat') or category.startswith('pcmcat'):
                    filters.append(f'categoryPath.id={category}')
                    logger.info(f"Using category ID filter: {category}")
                else:
                    filters.append(f'categoryPath.name="{urllib.parse.quote(category)}"')
                    logger.info(f"Using category name filter: {category}")
            
            # Base search query (after manufacturer filter)
            if query:
                filters.append(f"search={urllib.parse.quote(query)}")
            
            # Price range filter (using salePrice attribute)
            if min_price is not None and max_price is not None:
                filters.append(f"salePrice>={min_price}")
                filters.append(f"salePrice<={max_price}")
            elif min_price is not None:
                filters.append(f"salePrice>={min_price}")
            elif max_price is not None:
                filters.append(f"salePrice<={max_price}")
            
            # Boolean filters
            if on_sale is True:
                filters.append("onSale=true")
            
            if free_shipping is True:
                filters.append("freeShipping=true")
            
            if in_store_pickup is True:
                filters.append("inStoreAvailability=true")
            
            # Construct URL with Best Buy API format: products(filter1=value1&filter2=value2)
            filter_str = "&".join(filters)
            url = f"{self.base_url}/v1/products({filter_str})" if filters else f"{self.base_url}/v1/products"
            
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "pageSize": min(page_size * 10, 100)  # Request 10x to get past gift cards/warranties (max 100)
            }
            # Add sort parameter if specified
            if sort:
                params["sort"] = sort
            elif category == 'abcat0700000':
                # Game Consoles category: sort by salePrice descending so expensive hardware
                # (consoles $450-$550) floats above cheap game titles ($20-$70) in results.
                # bestSellingRank.asc puts popular GAMES (Forza, Halo) before consoles.
                params["sort"] = "salePrice.desc"
                logger.info("Game console category search: using salePrice.desc to surface hardware")
            else:
                # Use bestSellingRank to prioritize popular devices over gift cards
                params["sort"] = "bestSellingRank.asc"
            
            # Add show parameter to request specific fields
            params["show"] = "sku,name,regularPrice,salePrice,onSale,image,largeFrontImage,mediumImage,thumbnailImage,longDescription,shortDescription,manufacturer,modelNumber,upc,url,addToCartUrl,customerReviewAverage,customerReviewCount,customerTopRated,freeShipping,inStoreAvailability,onlineAvailability,depth,height,width,weight,color,condition,preowned,dollarSavings,percentSavings"
            
            logger.info(f"Advanced search with filters: {filter_str if filters else 'none'}")
            logger.debug(f"Request URL: {url}")
            logger.debug(f"Request params: {params}")
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            total = data.get("total", 0)
            products = [Product.model_validate(p) for p in data.get("products", [])]
            
            logger.info(f"Advanced search found {total} products, returning {len(products)}")
            
            # Apply intelligent filtering if query provided
            if query and products:
                result = ProductSearchResponse(
                    total=total,
                    products=products,
                    from_=data.get("from", 1),
                    to=data.get("to", len(products)),
                    current_page=data.get("currentPage", 1),
                    total_pages=data.get("totalPages", 1)
                )
                return self._filter_and_rank_results(query, result, page_size)
            
            # Return without filtering
            return ProductSearchResponse(
                total=len(products[:page_size]),
                products=products[:page_size],
                from_=1,
                to=min(page_size, len(products)),
                current_page=1,
                total_pages=1
            )
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in advanced search: {e}")
            return ProductSearchResponse(total=0, products=[], from_=1, to=0, current_page=1, total_pages=0)
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return ProductSearchResponse(total=0, products=[], from_=1, to=0, current_page=1, total_pages=0)
    
    async def get_categories(
        self,
        category_id: Optional[str] = None,
        page_size: int = 100
    ) -> CategorySearchResponse:
        """
        Get Best Buy categories from Categories API
        Can retrieve all categories or search for specific ones
        
        Args:
            category_id: Optional category ID to filter (e.g., 'abcat0400000')
            page_size: Number of results per page (default 100, max 100)
            
        Returns:
            CategorySearchResponse with list of categories
            
        Example:
            # Get all categories
            result = await client.get_categories()
            
            # Get specific category
            result = await client.get_categories(category_id="abcat0400000")
        """
        try:
            # Check cache first
            if category_id and category_id in self._category_cache:
                logger.info(f"Returning cached category: {category_id}")
                cached_cat = self._category_cache[category_id]
                return CategorySearchResponse(
                    total=1,
                    categories=[cached_cat],
                    from_=1,
                    to=1,
                    current_page=1,
                    total_pages=1
                )
            
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Build URL
            if category_id:
                url = f"{self.base_url}/v1/categories(id={category_id})"
            else:
                url = f"{self.base_url}/v1/categories"
            
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "pageSize": min(page_size, 100),
                "show": "id,name,url,path,subCategories"
            }
            
            logger.info(f"Getting categories: {url}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            total = data.get("total", 0)
            categories = [Category(**cat) for cat in data.get("categories", [])]
            
            # Cache retrieved categories
            for cat in categories:
                self._category_cache[cat.id] = cat
            
            logger.info(f"Found {total} categories, returning {len(categories)}")
            
            return CategorySearchResponse(
                total=total,
                categories=categories,
                from_=data.get("from", 1),
                to=data.get("to", len(categories)),
                current_page=data.get("currentPage", 1),
                total_pages=data.get("totalPages", 1)
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting categories: {e}")
            return CategorySearchResponse(total=0, categories=[], from_=1, to=0, current_page=1, total_pages=0)
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return CategorySearchResponse(total=0, categories=[], from_=1, to=0, current_page=1, total_pages=0)
    
    async def search_categories(
        self,
        name: str,
        page_size: int = 20
    ) -> CategorySearchResponse:
        """
        Search for categories by name using wildcards
        
        Args:
            name: Category name to search (supports wildcards with *)
            page_size: Number of results per page (default 20, max 100)
            
        Returns:
            CategorySearchResponse with matching categories
            
        Example:
            # Search for camera categories
            result = await client.search_categories(name="Camera*")
            
            # Search for phone categories
            result = await client.search_categories(name="Phone*")
        """
        try:
            # Normalize name for cache lookup (remove wildcard, lowercase)
            cache_key = name.lower().rstrip('*').strip()
            
            # Check if this is a common category (use COMMON_CATEGORIES)
            if cache_key in COMMON_CATEGORIES:
                category_id = COMMON_CATEGORIES[cache_key]
                logger.info(f"Using cached common category ID for '{name}': {category_id}")
                return await self.get_categories(category_id=category_id)
            
            # Check search cache (for non-common categories)
            if cache_key in self._search_cache:
                logger.info(f"Returning cached search results for '{name}'")
                return self._search_cache[cache_key]
            
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Build search query
            # Use wildcard if not provided
            search_name = name if '*' in name else f"{name}*"
            # Don't URL-encode wildcards (*) - Best Buy API requires them literally
            url = f"{self.base_url}/v1/categories(name={urllib.parse.quote(search_name, safe='*')})"
            
            params = {
                "apiKey": self.api_key,
                "format": "json",
                "pageSize": min(page_size, 100),
                "show": "id,name,url,path,subCategories"
            }
            
            logger.info(f"Searching categories with name: {search_name}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            total = data.get("total", 0)
            categories = [Category(**cat) for cat in data.get("categories", [])]
            
            # Create response
            response_obj = CategorySearchResponse(
                total=total,
                from_=data.get("from", 1),
                to=data.get("to", len(categories)),
                current_page=data.get("currentPage", 1),
                total_pages=data.get("totalPages", 1),
                categories=categories
            )
            
            # Cache individual categories
            for cat in categories:
                self._category_cache[cat.id] = cat
            
            # Cache search result (using normalized name)
            self._search_cache[cache_key] = response_obj
            
            logger.info(f"Found {total} categories matching '{name}', returning {len(categories)} (cached for future searches)")
            
            # Log first few results for debugging
            if categories:
                for i, cat in enumerate(categories[:3]):
                    logger.debug(f"{i+1}. {cat.name} (ID: {cat.id})")
            
            return response_obj
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching categories: {e}")
            return CategorySearchResponse(total=0, categories=[], from_=1, to=0, current_page=1, total_pages=0)
        except Exception as e:
            logger.error(f"Error searching categories: {e}")
            return CategorySearchResponse(total=0, categories=[], from_=1, to=0, current_page=1, total_pages=0)

    async def get_complementary_products(
        self,
        sku: str,
        category_hints: list = None,
        manufacturer_hint: str = None,
    ) -> List[Product]:
        """
        Sparky-like: Return products that complement the given SKU.

        API call budget: MAX 2 calls (critical for 5 req/min quota).
          Call 1 — alsoBought(sku): Best Buy's "bought together" signal.
                   If ≥ 3 results → return immediately (only 1 call used).
          Call 2 — search_products(targeted query): fired ONLY when alsoBought
                   returns < 3 results. Query derived from category_hints
                   (passed from user's Room DB history — NO extra get_product_by_sku call).

        Args:
            sku:               SKU of the anchor product.
            category_hints:    List of category names from user_context.recent_categories
                               (e.g. ["Televisions", "Home Theater"]).
            manufacturer_hint: Preferred brand from user_context.favorite_manufacturers[0].

        Returns:
            List of ≤ 6 complementary products; empty list on error or zero results.
        """
        try:
            seen_skus = {str(sku)}
            results: List[Product] = []

            # ── Call 1: alsoBought ──────────────────────────────────────────────
            also_bought = await self.get_also_bought(sku)
            for p in also_bought:
                p_sku = str(p.sku)
                if p_sku not in seen_skus:
                    seen_skus.add(p_sku)
                    results.append(p)
            logger.info(f"alsoBought({sku}) → {len(results)} product(s)")

            if len(results) >= 3:
                # Good enough — save Call 2 for other API needs
                return results[:6]

            # ── Call 2: targeted search (only when alsoBought gives < 3) ───────
            if category_hints:
                fallback_query = _get_complement_query(category_hints, manufacturer_hint)
            else:
                fallback_query = ""

            if fallback_query:
                logger.info(f"alsoBought insufficient ({len(results)}); searching '{fallback_query}'")
                try:
                    search_result = await self.search_products(fallback_query, page_size=6)
                    for p in search_result.products:
                        p_sku = str(p.sku)
                        if p_sku not in seen_skus:
                            seen_skus.add(p_sku)
                            results.append(p)
                    logger.info(f"search_products('{fallback_query}') → {len(search_result.products)} additional")
                except Exception as e:
                    logger.warning(f"search_products('{fallback_query}') failed: {e}")
            else:
                logger.info(f"No category_hints provided and alsoBought returned {len(results)} — returning as-is")

            logger.info(f"get_complementary_products({sku}): returning {len(results)} product(s) total")
            return results[:6]

        except Exception as e:
            logger.error(f"Error in get_complementary_products for SKU {sku}: {e}")
            return []

    async def get_open_box_options(self, sku: str) -> dict:
        """
        Check for open box (refurbished / Geek Squad Certified) offers for a SKU.
        Uses the Best Buy Buying Options (beta) API.
        Endpoint: GET /beta/products/{sku}/openBox
        Returns a dict with 'offers' list (each item has condition, prices.current, prices.regular)
        or an empty result set if no open box options are available.
        """
        try:
            await self.rate_limiter.acquire()
            url = f"{self.base_url}/beta/products/{sku}/openBox"
            params = {"apiKey": self.api_key}

            logger.info(f"Checking open box options for SKU: {sku}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                logger.info(f"No open box options found for SKU {sku}")
                return {"success": True, "has_open_box": False, "offers": []}

            # Extract the first (and usually only) result
            item = results[0]
            offers = item.get("offers", [])
            new_price = item.get("prices", {}).get("current")

            formatted_offers = [
                {
                    "condition": o.get("condition"),           # "excellent" | "certified"
                    "open_box_price": o.get("prices", {}).get("current"),
                    "regular_price": o.get("prices", {}).get("regular"),
                    "add_to_cart_url": item.get("links", {}).get("addToCart"),
                    "product_url": item.get("links", {}).get("web"),
                }
                for o in offers
            ]

            logger.info(f"Found {len(formatted_offers)} open box offer(s) for SKU {sku}")
            return {
                "success": True,
                "has_open_box": True,
                "new_price": new_price,
                "sku": sku,
                "product_name": item.get("names", {}).get("title"),
                "offers": formatted_offers,
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"No open box data for SKU {sku} (404)")
                return {"success": True, "has_open_box": False, "offers": []}
            logger.error(f"HTTP error checking open box for SKU {sku}: {e}")
            return {"success": False, "error": str(e), "offers": []}
        except Exception as e:
            logger.error(f"Error checking open box options for SKU {sku}: {e}")
            return {"success": False, "error": str(e), "offers": []}

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

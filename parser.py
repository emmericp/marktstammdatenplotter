import os
import json
import numpy as np
from glob import glob
from datetime import date, datetime, UTC
import re
from dataclasses import dataclass, asdict
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pyogrio import set_gdal_config_options
from dataclasses import dataclass
from datetime import date

def parse_dotnet_date(date_str):
    if not date_str:
        return None
    match = re.match(r"/Date\((\d+)\)/", date_str)
    if match:
        timestamp_ms = int(match.group(1))
        return datetime.fromtimestamp(timestamp_ms / 1000, UTC)

@dataclass
class PowerPlant:
    id: int
    num_panels: int
    power: float
    inverter: float
    install_date: date
    removal_date: date
    postal_code: str
    is_private: bool
    facing: int|str
    tilt: tuple[int, int]|str
    installation_type: str
    building_type: str
    owner_name: str
    energy_type: str
    longitude: float
    latitude: float
    off_shore: str|None

    @classmethod
    def from_json(cls, entry: dict):
        inverter_power = entry["Nettonennleistung"]
        match entry["Leistungsbegrenzung"]:
            case 805:
                inverter_power *= 0.5
            case 804:
                inverter_power *= 0.6
            case 803:
                inverter_power *= 0.7
            case 802: # "No"
                pass
            case 1535: # "Sonstige"
                pass # Would be great if this wasn't an enum, right?
        facing = entry["HauptausrichtungSolarModule"]
        match facing:
            case 703:  # nachgeführt (tracked)
                facing = "tracked"
            case 695:  # Nord
                facing = 0
            case 696:  # Nord-Ost
                facing = 45
            case 702:  # Nord-West
                facing = 315
            case 697:  # Ost
                facing = 90
            case 704:  # Ost-West (East-West) - This implies a range or general alignment.
                facing = "east-west"
            case 699:  # Süd
                facing = 180
            case 698:  # Süd-Ost
                facing = 135
            case 700:  # Süd-West
                facing = 225
            case 701:  # West
                facing = 270
            case _:
                facing = None
        tilt = entry["HauptneigungswinkelSolarmodule"]
        match tilt:
            case 810:  # < 20 Grad
                tilt = (0, 19)  # Represents a range from 0 to less than 20 degrees
            case 807:  # > 60 Grad
                tilt = (61, 90) # Represents a range from more than 60 to 90 degrees (vertical)
            case 809:  # 20 - 40 Grad
                tilt = (20, 40)
            case 808:  # 40 - 60 Grad
                tilt = (40, 60)
            case 806:  # Fassadenintegriert (Facade-integrated)
                tilt = 90 # This is a descriptive state, not a specific angle
            case 811:  # Nachgeführt (Tracked)
                tilt = "tracked" # This implies dynamic adjustment, not a fixed angle
            case _:
                tilt = None  # Handle unknown or unmapped values
        installation_type = entry["ArtDerSolaranlageId"]
        match installation_type:
            case 853:
                installation_type = "building"
            case 2484:
                installation_type = "building_other"
            case 852:
                installation_type = "free"
            case 3002:
                installation_type = "water"
            case 3058:
                installation_type = "parking_lot"
            case 2961:
                installation_type = "balkonkraftwerk"
            case _:
                installation_type = None
        power = entry["Bruttoleistung"]
        panels = entry["AnzahlSolarModule"]
        if panels and power / panels <= 0.1:
            panels = None
        building_type = entry["NutzungsbereichGebSA"]
        match building_type:
            case 714:
                building_type = "commercial"
            case 713:
                building_type = "household"
            case 715:
                building_type = "industry"
            case 716:
                building_type = "farming"
            case 717:
                building_type = "public"
            case 718:
                building_type = "other"
            case _:
                building_type = None  # Handle unknown or unmapped values
        off_shore = None
        if entry["WindAnLandOderSeeId"] == 889:
            if entry["StandortAnonymisiert"].startswith("Ostsee"):
                off_shore = "Ostsee"
            elif entry["StandortAnonymisiert"].startswith("Nordsee"):
                off_shore = "Nordsee"
        return cls(
            id=entry["Id"],
            num_panels=panels,
            power=power,
            inverter=inverter_power,
            install_date=parse_dotnet_date(entry["InbetriebnahmeDatum"]),
            removal_date=parse_dotnet_date(entry["EndgueltigeStilllegungDatum"]),
            postal_code=entry["Plz"],
            is_private=entry["AnlagenbetreiberPersonenArt"] == 518,
            facing=facing,
            tilt=tilt,
            installation_type=installation_type,
            building_type=building_type,
            owner_name=entry["AnlagenbetreiberName"],
            energy_type=entry["EnergietraegerName"],
            longitude=entry["Laengengrad"],
            latitude=entry["Breitengrad"],
            off_shore=off_shore,
        )


def load_data(data_dir, max_files=1000000):
    merged_data = []
    json_files = sorted(glob(os.path.join(data_dir, "*.json")))[:max_files]
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)
            for entry in content["Data"]:
                bkw = PowerPlant.from_json(entry)
                if bkw:
                    merged_data.append(bkw)
    print(f"Entries loaded from files: {len(merged_data)}")
    return merged_data

import json
from typing import List, Tuple
from .models import ValheimItem, ValheimMob

class DataParser:
    def __init__(self, json_path: str):
        self.json_path = json_path

    def load_raw_data(self) -> dict:
        """JSONを読み込むロジックをここに書く"""
        pass

    def parse_items(self, raw_data: dict) -> List[ValheimItem]:
        """生データからValheimItemのリストを作る"""
        pass

    def parse_mobs(self, raw_data: dict) -> List[ValheimMob]:
        """生データからValheimMobのリストを作る"""
        pass
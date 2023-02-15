import sqlite3
import json
import os
from typing import List, Dict, Union, Any


class GameData:
    def __init__(self):
        data_path = os.path.join(os.path.dirname(__file__), "data.json")
        f = open(data_path, mode='r', encoding='utf-8')
        data = json.load(f)
        self.teams = data['teams']
        self.levels = data['levels']
        self.light_status = ["通明", "摇曳", "暗淡", "寂灭"]
        # self.nodes = ["新层级", "漂流秘匣", "诡意行商", "消失的习俗", "诸王不再", "医者之志", "狂徒妄念", "重返家园", "信念"]
        self.nodes = ["新层级", "漂流秘匣", "诡意行商", "消失的习俗", "诸王不再", "医者之志"]
        self.calls = data['calls']
        self.enlightenments = data['enlightenments']
        self.rejections = data['rejections']
        db_path = os.path.join(os.path.dirname(__file__), "data.db")
        self.conn = sqlite3.connect(db_path)

    async def get_collection(self, sql) -> List[Union[str, str]]:
        cursor = self.conn.cursor()
        cursor.execute(f"{sql}")
        return cursor.fetchall()

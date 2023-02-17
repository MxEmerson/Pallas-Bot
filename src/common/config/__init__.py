import pymongo
import time
from pymongo.collection import Collection
from abc import ABC
from typing import Any, Optional

KEY_JOINER = '.'


class Config(ABC):
    _config_mongo: Optional[Collection] = None
    _table: Optional[str] = None
    _key: Optional[str] = None

    @classmethod
    def _get_config_mongo(cls) -> Collection:
        if cls._config_mongo is None:
            mongo_client = pymongo.MongoClient('127.0.0.1', 27017, w=0)
            mongo_db = mongo_client['PallasBot']
            cls._config_mongo = mongo_db[cls._table]
            cls._config_mongo.create_index(name='{}_index'.format(cls._key),
                                           keys=[(cls._key, pymongo.HASHED)])
        return cls._config_mongo

    _db_filter: Optional[dict] = None
    _document_key: Optional[int] = None
    _document_cache: Optional[dict] = None

    @classmethod
    def _find(cls, key: str) -> Any:
        if cls._document_key not in cls._document_cache:
            # 获取这个 key_id（bot_id 或 group_id）的所有配置（document）
            info = cls._get_config_mongo().find_one(cls._db_filter)
            cls._document_cache[cls._document_key] = info

        cache = cls._document_cache[cls._document_key]
        for k in key.split(KEY_JOINER):
            if cache and k in cache:
                cache = cache[k]
            else:
                return None

        return cache

    @classmethod
    def _update(cls, key: str, value: Any, db: bool = True) -> None:
        if db:
            cls._get_config_mongo().update_one(
                cls._db_filter, {'$set': {key: value}})

        if cls._document_key not in cls._document_cache:
            cls._document_cache[cls._document_key] = {}
        cache = cls._document_cache[cls._document_key]
        splited_keys = key.split(KEY_JOINER)
        for k in splited_keys[:-1]:
            if k not in cache:
                cache[k] = {}
            cache = cache[k]
        cache[splited_keys[-1]] = value

    def __init__(self, table: str, key: str, key_id: int) -> None:
        self.__class__._table = table
        self.__class__._key = key
        self.__class__._document_key = key_id
        self.__class__._db_filter = {key: key_id}
        if self.__class__._document_cache is None:
            self.__class__._document_cache = {}


class BotConfig(Config):
    def __init__(self, bot_id: int, group_id: int = 0, cooldown: int = 5) -> None:
        super().__init__(
            table='config',
            key='account',
            key_id=bot_id)

        self.bot_id = bot_id
        self.group_id = group_id
        self.cooldown = cooldown

    def security(self) -> bool:
        '''
        账号是否安全（不处于风控等异常状态）
        '''
        security = self._find('security')
        return True if security else False

    def auto_accept(self) -> bool:
        '''
        是否自动接受加群、加好友请求
        '''
        accept = self._find('auto_accept')
        return True if accept else False

    def is_admin_of_bot(self, user_id: int) -> bool:
        '''
        是否是管理员
        '''
        admins = self._find('admins')
        return user_id in admins if admins else False

    def is_cooldown(self, action_type: str) -> bool:
        '''
        是否冷却完成
        '''
        cd = self._find(
            f'cooldown{KEY_JOINER}{action_type}{KEY_JOINER}{self.group_id}')
        return cd + self.cooldown < time.time() if cd else True

    def refresh_cooldown(self, action_type: str) -> None:
        '''
        刷新冷却时间
        '''
        self._update(
            f'cooldown{KEY_JOINER}{action_type}{KEY_JOINER}{self.group_id}', time.time(), db=False)

    def reset_cooldown(self, action_type: str) -> None:
        '''
        重置冷却时间
        '''
        self._update(
            f'cooldown{KEY_JOINER}{action_type}{KEY_JOINER}{self.group_id}', 0, db=False)

    def drink(self) -> None:
        '''
        喝酒功能，增加牛牛的混沌程度（bushi
        '''
        self._update(f'drunk{KEY_JOINER}{self.group_id}',
                     self.drunkenness() + 1, db=False)

    def sober_up(self) -> bool:
        '''
        醒酒，降低醉酒程度，返回是否完全醒酒
        '''
        value = self.drunkenness() - 1
        self._update(f'drunk{KEY_JOINER}{self.group_id}', value, db=False)
        return value <= 0

    def drunkenness(self) -> int:
        '''
        获取醉酒程度
        '''
        value = self._find(f'drunk{KEY_JOINER}{self.group_id}')
        return value if value else 0

    @classmethod
    def fully_sober_up(cls) -> None:
        '''
        完全醒酒
        '''
        cls._update('drunk', {})

    def is_sleep(self) -> bool:
        '''
        牛牛睡了么？
        '''
        value = self._find(f'sleep{KEY_JOINER}{self.group_id}')
        return value > time.time() if value else False

    def sleep(self, seconds: int) -> None:
        '''
        牛牛睡觉
        '''
        self._update(f'sleep{KEY_JOINER}{self.group_id}',
                     time.time() + seconds)

    def taken_name(self) -> int:
        '''
        返回在该群夺舍的账号
        '''
        user_id = self._find(f'taken_name{KEY_JOINER}{self.group_id}')
        return user_id if user_id else 0

    def update_taken_name(self, user_id: int) -> None:
        '''
        更新夺舍的账号
        '''
        self._update(f'taken_name{KEY_JOINER}{self.group_id}', user_id)


class GroupConfig(Config):
    def __init__(self, group_id: int, cooldown: int = 5) -> None:
        super().__init__(
            table='group_config',
            key='group_id',
            key_id=group_id)

        self.group_id = group_id
        self.cooldown = cooldown

    def roulette_mode(self) -> int:
        '''
        获取轮盘模式

        :return: 0 踢人 1 禁言
        '''
        mode = self._find('roulette_mode')
        return mode if mode else 0

    def set_roulette_mode(self, mode: int) -> None:
        '''
        设置轮盘模式

        :param mode: 0 踢人 1 禁言
        '''
        self._update('roulette_mode', mode)

    def ban(self) -> None:
        '''
        拉黑该群
        '''
        self._update('banned', True)

    def is_banned(self) -> bool:
        '''
        群是否被拉黑
        '''
        banned = self._find('banned')
        return True if banned else False

    def is_cooldown(self, action_type: str) -> bool:
        '''
        是否冷却完成
        '''
        cd = self._find(
            f'cooldown{KEY_JOINER}{action_type}{KEY_JOINER}{self.group_id}')
        return cd + self.cooldown < time.time() if cd else True

    def refresh_cooldown(self, action_type: str) -> None:
        '''
        刷新冷却时间
        '''
        self._update(
            f'cooldown{KEY_JOINER}{action_type}{KEY_JOINER}{self.group_id}', time.time(), db=False)

    def reset_cooldown(self, action_type: str) -> None:
        '''
        重置冷却时间
        '''
        self._update(
            f'cooldown{KEY_JOINER}{action_type}{KEY_JOINER}{self.group_id}', 0, db=False)


class UserConfig(Config):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            table='user_config',
            key='user_id',
            key_id=user_id)

        self.user_id = user_id

    def ban(self) -> None:
        '''
        拉黑这个人
        '''
        self._update('banned', True)

    def is_banned(self) -> bool:
        '''
        是否被拉黑
        '''
        banned = self._find('banned')
        return True if banned else False

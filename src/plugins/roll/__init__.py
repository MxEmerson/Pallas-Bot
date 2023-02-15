import random
import asyncio

from nonebot import on_command, on_message
from nonebot.rule import Rule
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.adapters import Bot, Event
from nonebot.permission import Permission
from nonebot.permission import Permission
from nonebot.adapters.onebot.v11 import MessageSegment, Message, permission, GroupMessageEvent

from src.common.config import BotConfig, GroupConfig
from .game_data import GameData

gamedata = GameData()

target_msgs = ['牛牛掷骰', '牛牛roll']


async def message_equal(bot: Bot, event: Event, state: T_State) -> bool:
    raw_msg = event.raw_message
    for target in target_msgs:
        if target == raw_msg:
            return True
    return False

roll = on_message(
    rule=Rule(message_equal),
    priority=4,
    block=True,
    permission=permission.GROUP
)


def judge_dice(light: str, point: int) -> str:
    if light == "通明":
        if point >= 6:
            return "好运相随"
        else:
            return "一帆风顺"
    elif light == "摇曳":
        if point >= 4:
            return "一帆风顺"
        else:
            return "一波三折"
    elif light == "暗淡":
        if point >= 6:
            return "一帆风顺"
        else:
            return "一波三折"
    elif light == "寂灭":
        if point >= 6:
            return "一波三折"
        else:
            return "厄运缠身"


async def send_text(handle, context: list) -> bool:
    text_list = context
    if not text_list:
        return False

    for text in text_list:
        if not text:
            continue
        else:
            await asyncio.sleep(2.5)
        await handle.send(text)

    return True


@roll.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    # TODO:
    # 保存每个群的状态，实现简化版水月与深蓝之树

    config = GroupConfig(event.group_id, cooldown=60)
    if not config.is_cooldown("roll"):
        await roll.finish("正在返回陆地...请稍候片刻")
    config.refresh_cooldown("roll")
    await roll.send("正在潜入深海...")
    # 分队与藏品：骰子面数
    dice_level = 0
    team_name = random.choice(gamedata.teams)["name"]
    if team_name == "物尽其用分队":
        dice_level += 1
    # collection = random.sample(gamedata.collections, random.randint(1, 6))
    collection = []
    coll_ids = random.sample(range(1, 238), random.randint(1, 6))
    for coll_id in coll_ids:
        sql = f"select name, description, id from collections where id = {coll_id}"
        _coll = await gamedata.get_collection(sql)
        collection.append(_coll[0])
    collection_names = [c[0] for c in collection]
    collection_name = "，".join(collection_names)
    collection_ids = [str(c[2]) for c in collection]
    collection_id = ",".join(collection_ids)
    for item in collection:
        if item[0] == "鸭爵金砖":
            dice_level += 1
    dice_side = 6
    if dice_level == 2:
        dice_side = 12
    elif dice_level == 1:
        dice_side = 8
    # 灯火
    seed = random.randint(1, 100)
    light = "通明"
    light_description = "阴影退避，光芒闪耀。"
    light_num = 100
    if seed <= 5:
        light = "寂灭"
        light_num = 0
        light_description = "再无火焰，再无光明。"
    elif seed <= 15:
        light = "暗淡"
        light_num = 5*random.randint(1, 9)
        light_description = "光点微渺，阴影随行。"
    elif seed <= 30:
        light = "摇曳"
        light_num = 5*random.randint(10, 19)
        light_description = "烛火摇荡，光影同舞。"
    # light = random.choice(gamedata.light_status)
    # 节点
    node = random.choice(gamedata.nodes)
    # 掷骰
    point = random.randint(1, dice_side)
    # 事件
    event_content = ""
    result_content = ""
    # 判定
    if node == "新层级":
        level = random.choice(gamedata.levels)
        level_name = level["name"]
        level_notes = level["description"]
        if level_name == "绀碧摇篮":
            seed = random.randint(1, 10)
            if seed <= 5:
                light = "寂灭"
                light_num = 0
            else:
                light = "暗淡"
                light_num = 5*random.randint(1, 3)
        event_content = f"你到达了<{level_name}> - {level_notes}"
        status = judge_dice(light, point)
        call = None
        enlightenment = None
        enlightenment_name = None
        enlightenment_notes = None
        rejection = None
        rejection_name = None
        rejection_notes = None
        if light == "寂灭" or (light == "暗淡" and random.randint(1, 2) == 1):
            call = random.sample(gamedata.calls, 2)
        elif light == "暗淡" or (light == "摇曳" and random.randint(1, 4) == 1):
            call = random.sample(gamedata.calls, 1)
        elif light == "摇曳" or (light == "通明" and random.randint(1, 6) == 1):
            call = random.sample(gamedata.calls, 1)
        if status == "好运相随":
            enlightenment = random.choice(gamedata.enlightenments)
            enlightenment_name = enlightenment["name"]
            enlightenment_notes = enlightenment["description"]
            result_content += f"获得了启示<{enlightenment_name}>：“{enlightenment_notes}”"
        elif status == "一波三折" or status == "厄运缠身":
            rejection = random.choice(gamedata.rejections)
            rejection_name = rejection["name"]
            rejection_notes = rejection["description"]
            result_content += f"已触发的排异反应<{rejection_name}>：“{rejection_notes}”"
        elif status == "一帆风顺":
            result_content += "海潮平静，没有发生什么意外"
        if call != None:
            event_content += f"\n已触发的大群的呼唤："
            for c in call:
                call_name = c["name"]
                call_notes = c["description"]
                event_content += f"\n- “{call_name}”：“{call_notes}”"
    elif node == "漂流秘匣":
        event_content = "你获得了漂流秘匣，里面装着一些小东西。尝试开启漂流秘匣，你决定相信命运"
        if point >= 5:
            status = "一帆风顺"
            result_content += "漂流秘匣被打开了，顺利取走了里面的宝物："
            sql = f"select name, description, id from collections where title != '遭诅古物' and id not in ({collection_id}) order by random() limit 1"
            _collection = await gamedata.get_collection(sql)
            result_content += f"\n- {_collection[0][0]}：{_collection[0][1]}"
        else:
            status = "一波三折"
            result_content += "秘匣在命运中逆流而去，只散落下几枚硬币"
    elif node == "诡意行商":
        event_content = "不是盟友也不是敌人，有些人喜欢站在中间。"
        # if random.randint(1, 6) == 1:
        #     event_content = '你想"请"坎诺特"降价"'
        if point >= 7:
            status = "好运相随"
            result_content += "坎诺特愿意为你提供一点“高级货”："
            sql = f"select name, description from collections where value = 2 and title != '遭诅古物' and id not in ({collection_id}) order by random() limit 2"
            _collection = await gamedata.get_collection(sql)
            for c in _collection:
                result_content += f"\n- {c[0]}：{c[1]}"
        elif point >= 5:
            status = "一帆风顺"
            result_content += "坎诺特愿意展示一批新到的货物："
            sql = f"select name, description from collections where value = 1 and title != '遭诅古物' and id not in ({collection_id}) order by random() limit 2"
            _collection = await gamedata.get_collection(sql)
            for c in _collection:
                result_content += f"\n- {c[0]}：{c[1]}"
        else:
            status = "风平浪静"
            result_content += "坎诺特拿出了两件新的货物："
            sql = f"select name, description from collections where value = 0 and title != '遭诅古物' and id not in ({collection_id}) order by random() limit 2"
            _collection = await gamedata.get_collection(sql)
            for c in _collection:
                result_content += f"\n- {c[0]}：{c[1]}"
    elif node == "消失的习俗":
        event_content = "在捕鳞船还能航行的日子，伊比利亚沿海村庄的儿童们会向出海的父母许愿得到一件礼物，待到大人们渔获归来，他们会将最大的一条鳞鱼亲手交给儿女，而之前孩童们许愿的礼品，或是一些其他惊喜，就藏在鱼腹里。听说在富贵人家，孩子可以许下不止一个愿望，可现在呢，在你面前的只有几条贴着许愿条的风干鳞鱼。"
        sql = f"select name, description from collections where value = 1 and title != '遭诅古物' and id not in ({collection_id}) order by random() limit 1"
        _collection = await gamedata.get_collection(sql)
        sql = f"select name, description from collections where title != '遭诅古物' and id not in ({collection_id}) order by random() limit 5"
        _collection += await gamedata.get_collection(sql)
        _i_range = [0, 2, 4] if team_name == "物尽其用分队" else [0, 2]
        for i in _i_range:
            _bonus = "从桌子底下" if i == 4 else ""
            event_content += f"\n{_bonus}取走这条贴着许愿条的鳞鱼 - {_collection[i][0]}"
        if point >= 6:
            status = "好运相随"
            result_content += "虔诚让命运愿意多给一份馈赠。你获得了："
            _j_range = random.choice(_i_range)
            for j in [_j_range, _j_range + 1]:
                result_content += f"\n- {_collection[j][0]}：{_collection[j][1]}"
        elif point > 1:
            status = "一帆风顺"
            result_content += "虔诚的人总能获得想要的。你获得了："
            j = random.choice(_i_range)
            result_content += f"\n- {_collection[j][0]}：{_collection[j][1]}"
        else:
            status = "一波三折"
            result_content += "那件收藏品不在你的命运之中。你获得了："
            sql = f"select name, description from collections where title != '遭诅古物' and id not in ({collection_id}) order by random() limit 2"
            _collection = await gamedata.get_collection(sql)
            result_content += f"\n- {_collection[0][0]}：{_collection[0][1]}"
    elif node == "诸王不再":
        event_content = "你找到了一座空荡荡的伊比利亚城市，这里既没有人，也没有恐鱼的踪迹。在这座城市中央，矗立着一座宏伟的博物馆。你阅览了几近风化的传单，发现这座博物馆是为了纪念伊比利亚的无名诸王们而建的。"
        sql = f"select name, description from collections where value = 1 and id in (114, 126, 127, 128, 202) and id not in ({collection_id}) order by random() limit 1"
        _collection = await gamedata.get_collection(sql)
        if point > 5:
            status = "一帆风顺"
            result_content += "一番搜寻之后，你找到了一个盒子。旁边的石碑上刻录着一位先王的丰功伟绩。至于财宝？这个空盒子就是他留下的财宝，或者说，他流传给后人的珍贵印象。在那空荡荡的盒中，包含着伊比利亚王室对立国诸王们的无限尊崇。\n诸王的宝藏现在是你的了："
            result_content += f"\n- {_collection[0][0]}：{_collection[0][1]}"
        else:
            status = "一波三折"
            result_content += "你并没有看到特别值得获取的财宝，或许有价值的东西早就被王室仆从或审判庭拿走了吧......而且这里根本就没有国王们的塑像，甚至连姓名或称号都没有。你不禁开始怀疑这个所谓的博物馆中各种信息的真实性。\n一番搜寻之后，你空手而归，只能拿过一旁的破烂导览册当作收获。这些王离现在这个时代太过久远，名号、称呼、纹章、代表器物尽皆散佚在历史中，伊比利亚人只能将他们作为一个整体，一遍又一遍复述着远古往昔流传至今的只言片语。"
    elif node == "医者之志":
        event_content += "海岸吞噬陆地，文明也随之衰颓。学识成为奇术，而无知者遍行大地。你遇见一位伊比利亚行医，他正独自为患者采摘草药，见你“武装精良”，他恳请你保护他的人身安全。你答应了。"
        result_content += "你和他相谈甚欢，从药草的疗效到人类的未来皆有涉猎。他惊讶于你的学识，似乎认定你能够做些什么。思忖再三后，他从包裹里取出些物品交给你。他说这些物品曾是一位圣徒的遗物，圣徒魂归故里，村庄的人们便将遗物当作圣物供奉。然而老圣徒的遗愿是这些物品能够传承下去，为伊比利亚带去希望，而非束之高阁，蒙尘落灰。见你接过了物件，行医向你道谢，随后返回了村庄。\n你获得了："
        if point > 5:
            status = "一帆风顺"
            sql = f"select name, description from collections where value = 1 and title != '遭诅古物' and id not in ({collection_id}) order by random() limit 1"
        else:
            status = "风平浪静"
            sql = f"select name, description from collections where value = 0 and title != '遭诅古物' and id not in ({collection_id}) order by random() limit 1"
        _collection = await gamedata.get_collection(sql)
        sql = f"select name, description from collections where id = 195"
        _collection += await gamedata.get_collection(sql)
        for c in _collection:
            result_content += f"\n- {c[0]}：{c[1]}"
    
    # 生成消息
    msg = [
        f"你的分队：{team_name}\n你拥有的的藏品：{collection_name}\n你的灯火状态：{light_num} - <{light}> - {light_description}\n你的骰子：{dice_side}面骰子", 
        f"正在进入节点：{node}", 
        f"{event_content}", 
        f"{status}：你掷出了{point}点", 
        f"{result_content}"
    ]
    ret = await send_text(roll, msg)
    if not ret:
        await roll.finish("风浪卷住你的脚踝，轻轻将你拉离陆地，拥入它的怀抱。（未知错误）")
    else:
        await roll.finish("水月与博士的探索仍在继续...稍后片刻方可继续掷骰。")

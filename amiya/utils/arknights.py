import json
import logging
import random

import requests
from fuzzywuzzy.fuzz import ratio


def fetch(url):
    """
    Fetch data from Github
    """
    data = requests.get(url)
    if data.status_code != 200:
        logging.error("Fetching failed")
        return None
    data = data.json()
    return data


operator_table = None


def get_operator_info(operator):
    """
    Returns operator info by ID or name
    """
    global operator_table
    if operator_table is None:
        with open("ArknightsData/en-US/gamedata/excel/character_table.json", "r") as f:
            operator_table = json.load(f)
    return max(
        list(operator_table.items()),
        key=lambda x: max(
            ratio(x[0], operator),
            ratio(x[1]["name"], operator),
            ratio(x[1]["appellation"] or "", operator),
        ),
    )[1]


skin_table = None


def get_operator_skins(operator):
    """
    Returns operator skins
    """
    info = get_operator_info(operator)
    char_id = info["phases"][0]["characterPrefabKey"]
    global skin_table
    if skin_table is None:
        with open("ArknightsData/en-US/gamedata/excel/skin_table.json", "r") as f:
            skin_table = json.load(f)
    skin_list = skin_table["charSkins"]
    return [skin for skin in skin_list.values() if skin["charId"] == char_id]


skill_table = None


def get_operator_skills(operator):
    """
    Returns operator skills
    """
    info = get_operator_info(operator)
    skills = operator["skills"]
    global skill_table
    if skill_table is None:
        with open("ArknightsData/en-US/gamedata/excel/skill_table.json", "r") as f:
            skill_table = json.load(f)
    return [(skill, skill_table[skill["skillId"]]) for skill in skills]


hidden_table = None


def get_operator_by_tags(tags):
    """
    Returns operators that have specified tags
    """
    url = "https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/json/akhr.json"
    global operator_table, hidden_table
    if operator_table is None:
        with open("ArknightsData/en-US/gamedata/excel/character_table.json", "r") as f:
            operator_table = json.load(f)
    if hidden_table is None:
        hidden_table = fetch(url)
    hidden_list = [{x["name"]: x["hidden"]} for x in hidden_table]
    profession_table = {
        "CASTER": "Caster",
        "TANK": "Defender",
        "WARRIOR": "Guard",
        "MEDIC": "Medic",
        "SNIPER": "Sniper",
        "SPECIAL": "Specialist",
        "SUPPORT": "Supporter",
        "TOKEN": "Token",
        "TRAP": "Trap",
        "PIONEER": "Vanguard",
    }
    operator_list = [
        {key: x[key] for key in ["name", "position", "tagList", "rarity", "profession"]}
        for x in operator_table.values()
        if (
            (
                x["tagList"] is not None
                and (set([i.lower() for i in x["tagList"]]) & set(tags))
            )
            or x["position"].lower() in tags
            or profession_table[x["profession"]].lower() in tags
            or ("senior operator" in tags and x["rarity"] == 4)
            or ("top operator" in tags and x["rarity"] == 5)
        )
        and {x["name"]: False} in hidden_list
    ]
    for operator in operator_list:
        operator["tagList"].append(operator.pop("position", None).title())
        operator["tagList"].append(
            profession_table[operator.pop("profession", None)].title()
        )
        if operator["rarity"] == 4:
            operator["tagList"].append("Senior Operator")
        if operator["rarity"] == 5:
            operator["tagList"].append("Top Operator")
    return operator_list


item_table = None


def get_item(item):
    """
    Returns item info by name or ID
    """
    global item_table
    if item_table is None:
        with open("ArknightsData/en-US/gamedata/excel/item_table.json", "r") as f:
            item_table = json.load(f)
    item_list = item_table["items"]
    return max(
        list(item_list.values()),
        key=lambda x: max(ratio(x["name"], item), ratio(x["itemId"], item)),
    )


stage_table = None


def get_stage(stage):
    """
    Returns stage info by ID or name
    """
    global stage_table
    if stage_table is None:
        with open("ArknightsData/en-US/gamedata/excel/stage_table.json", "r") as f:
            stage_table = json.load(f)
    stage_list = stage_table["stages"]
    name = " ".join([x for x in stage if x[0] != "+"])
    match = max(
        list(stage_list.values()),
        key=lambda x: max(
            ratio(x["stageId"], name),
            ratio(x["code"], name),
            ratio(x["name"] or "", name),
        ),
    )
    if "+cm" in stage:
        if match["hardStagedId"] is not None:
            match = stage_list[match["hardStagedId"]]
    return match


def get_stage_with_item(id):
    """
    Returns stages that drop item
    """
    global stage_table
    if stage_table is None:
        with open("ArknightsData/en-US/gamedata/excel/stage_table.json", "r") as f:
            stage_table = json.load(f)
    stage_list = stage_table["stages"]

    def get_index(lst):
        return next((idx for (idx, dt) in enumerate(lst) if dt["id"] == id), None)

    return [
        (
            x,
            x["stageDropInfo"]["displayDetailRewards"][
                get_index(x["stageDropInfo"]["displayDetailRewards"])
            ]["dropType"],
        )
        for x in list(stage_list.values())
        if get_index(x["stageDropInfo"]["displayDetailRewards"]) is not None
    ]


building_data = None


def get_furniture(furniture):
    """
    Returns furniture by ID or name
    """
    global building_data
    if building_data is None:
        with open("ArknightsData/en-US/gamedata/excel/building_data.json", "r") as f:
            building_data = json.load(f)
    furniture_list = building_data["customData"]["furnitures"]
    return max(
        list(furniture_list.values()),
        key=lambda x: max(ratio(x["name"], furniture), ratio(x["id"], furniture)),
    )


enemy_handbook_table = None


def get_enemy(enemy):
    """
    Returns enemy by ID or name
    """
    global enemy_handbook_table
    if enemy_handbook_table is None:
        with open(
            "ArknightsData/en-US/gamedata/excel/enemy_handbook_table.json", "r"
        ) as f:
            enemy_handbook_table = json.load(f)
    return max(
        list(enemy_handbook_table.values()),
        key=lambda x: max(ratio(x["name"], enemy), ratio(x["enemyId"], enemy)),
    )


tip_table = None


def get_tips(category):
    """
    Returns tips
    """
    global tip_table
    if tip_table is None:
        with open("ArknightsData/en-US/gamedata/excel/tip_table.json", "r") as f:
            tip_table = json.load(f)
    tip_list = tip_table["tips"]
    if category == None:
        return random.choice(tip_list)
    else:
        return random.choice([x for x in tip_list if x["category"] == category.upper()])

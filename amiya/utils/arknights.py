"""
Arknights data parsing
Return logic for every function: Get the value with highest Levenshtein Distance between input and name, ID (or code, appellation)
"""

import json
import logging
import random
from typing import Optional, Tuple

import requests
# Fuzzy String Matching
from fuzzywuzzy.fuzz import ratio

from amiya.utils import constants


def fetch(url: str) -> dict:
    """
    Grabs json data from Github link

    Args:
        url (str): Github raw file url

    Returns:
        dict: A json that contains the results
    """

    # Using requests to fetch data
    data = requests.get(url)

    # If an error occurred during fetching
    if data.status_code != 200:
        logging.error("Fetching failed")
        return None

    # Parses data to json (dict)
    data = data.json()
    return data


operator_table = None


def get_operator_info(operator: str) -> dict:
    """
    Grabs operator detailed info (search by name, ID or appellation)

    Args:
        operator (str): Operator name, ID or appellation

    Returns:
        dict: A json that contains the operator info with ID, name or appellation that matches the parameter
    """

    global operator_table
    # Check if operator_table is already loaded and load it from local file
    if operator_table is None:
        with open("ArknightsData/en-US/gamedata/excel/character_table.json", "r") as f:
            operator_table = json.load(f)

    return max(
        list(operator_table.items()),
        key=lambda x: max(
            # Match ID
            ratio(x[0], operator),
            # Match name
            ratio(x[1]["name"], operator),
            # Match appellation
            ratio(x[1]["appellation"] or "", operator),
        ),
    )[1]


skin_table = None


def get_operator_skins(operator: str) -> list:
    """
    Grabs operator skins detailed infos (search by operator name, ID or appellation)

    Args:
        operator (str): Operator name, ID or appellation

    Returns:
        list: A list of dict that contains the operator skins with ID, name or appellation that matches the parameter
    """

    # Search for operator
    info = get_operator_info(operator)
    # Get default skin ID
    char_id = info["phases"][0]["characterPrefabKey"]

    # Check if skin_table is already loaded and load it from local file
    global skin_table
    if skin_table is None:
        with open("ArknightsData/en-US/gamedata/excel/skin_table.json", "r") as f:
            skin_table = json.load(f)

    # Get list of operator skins mapped by skin ID
    skin_list = skin_table["charSkins"]
    return [skin for skin in skin_list.values() if skin["charId"] == char_id]


skill_table = None


def get_operator_skills(operator: str) -> list:
    """
    Grabs operator skills detailed infos (search by operator name, ID or appellation)

    Args:
        operator (str): Operator name, ID or appellation

    Returns:
        list: A list of tuple (skill from character_table, skill from skill_table) that contains the operator skills with ID, name or appellation that matches the parameter
    """

    # Search for operator
    info = get_operator_info(operator)
    # Get operator skills
    skills = operator["skills"]

    # Check if skill_table is already loaded and load it from local file
    global skill_table
    if skill_table is None:
        with open("ArknightsData/en-US/gamedata/excel/skill_table.json", "r") as f:
            skill_table = json.load(f)

    # Return a list of tuple with skill info from operator_table and skill_table
    # As for why, the skill data from 2 tables are different but both useful
    return [(skill, skill_table[skill["skillId"]]) for skill in skills]


hidden_table = None


def get_operator_by_tags(tags: list) -> list:
    """
    Grabs operators that contains given tags

    Args:
        tags (list): The input tags list (input must be correct)

    Returns:
        list: A list of dict that contains operator's name, position (Ranged or Melee), tag list. rarity and profession
    """

    url = "https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/json/akhr.json"
    # Check if operator_table and hidden_table is already loaded and load it
    # from local file or fetch it
    global operator_table, hidden_table
    if operator_table is None:
        with open("ArknightsData/en-US/gamedata/excel/character_table.json", "r") as f:
            operator_table = json.load(f)
    if hidden_table is None:
        hidden_table = fetch(url)

    # As the operator_table doesn't actually show which operator we can't get from recruitment, we need Aceship's akhr file to check
    # Even though in character_table.json there's a key named
    # "itemOptainApproach", I don't use it to check because it's faulty (?) as
    # Indra is supposed to be a Recruitment only operator but it shows
    # "Recruitment & Headhunting" in her "itemOptainApproach"
    hidden_list = [{x["name"]: x["hidden"]} for x in hidden_table]

    # The actual work
    operator_list = [
        # Grabbing only what we need
        {key: x[key]
            for key in ["name", "position", "tagList", "rarity", "profession"]}
        for x in operator_table.values()
        if (
            (
                # Check for common tags
                x["tagList"] is not None
                and (set([i.lower() for i in x["tagList"]]) & set(tags))
            )
            # Check for position
            or x["position"].lower() in tags
            # Check for profession
            or constants.PROFESSION_TABLE[x["profession"]].lower() in tags
            # Check for Senior or Top Operator by rarity (0-indexed)
            or ("senior operator" in tags and x["rarity"] == 4)
            or ("top operator" in tags and x["rarity"] == 5)
        )
        # If operator is not in hidden_list, that means we can obtain through
        # Recruitment
        and {x["name"]: False} in hidden_list
    ]
    # Append the remaining tags as the tagList doesn't contain position,
    # profession or rarity
    for operator in operator_list:
        operator["tagList"].append(operator.pop("position", None).title())
        operator["tagList"].append(
            constants.PROFESSION_TABLE[operator.pop(
                "profession", None)].title()
        )
        if operator["rarity"] == 4:
            operator["tagList"].append("Senior Operator")
        if operator["rarity"] == 5:
            operator["tagList"].append("Top Operator")

    return operator_list


item_table = None


def get_item(item: str) -> dict:
    """
    Grabs detailed item info (search by name or ID)

    Args:
        item (str): Item name or ID

    Returns:
        dict: A dict that contains item info with name or ID that matches the parameter
    """

    # Check if item_table is already loaded and load it from local file
    global item_table
    if item_table is None:
        with open("ArknightsData/en-US/gamedata/excel/item_table.json", "r") as f:
            item_table = json.load(f)

    # Get item list from table
    item_list = item_table["items"]
    return max(
        list(item_list.values()),
        # Match name or ID
        key=lambda x: max(ratio(x["name"], item), ratio(x["itemId"], item)),
    )


stage_table = None


def get_stage(stage: str) -> Tuple[dict, dict]:
    """
    Grabs detailed stage info (search by name, code or ID)

    Args:
        stage (str): Stage name, code or ID

    Returns:
        Tuple[dict, dict]: A tuple of dict that contains stage info with name, code or ID that matches the parameter
    """

    # Check if stage_table is already loaded and load it from local file
    global stage_table
    if stage_table is None:
        with open("ArknightsData/en-US/gamedata/excel/stage_table.json", "r") as f:
            stage_table = json.load(f)

    # Get stage list
    stage_list = stage_table["stages"]

    stage_info = max(
        list(stage_list.values()),
        key=lambda x: max(
            # Match ID
            ratio(x["stageId"], stage),
            # Match code
            ratio(x["code"], stage),
            # Match name
            ratio(x["name"] or "", stage),
        ),
    )

    stage_extra_info = None
    with open(f'ArknightsData/en-US/gamedata/levels/{stage_info["levelId"].lower()}.json', "r") as f:
        stage_extra_info = json.load(f)

    return (stage_info, stage_extra_info)


def get_stage_with_item(id: str) -> list:
    """
    Grabs stages that drops item with id

    Args:
        id (str): Item ID (input must be correct)

    Returns:
        list: A list that contains tuple (stage that drop item with ID, probability of item dropping)
    """

    # Check if stage_table is already loaded and load it from local file
    global stage_table
    if stage_table is None:
        with open("ArknightsData/en-US/gamedata/excel/stage_table.json", "r") as f:
            stage_table = json.load(f)

    # Get stage list
    stage_list = stage_table["stages"]

    def get_index(lst: list) -> Optional[int]:
        """
        Get index of item that has the same ID with given ID in item drop list of stage
        Returns None if item is not in list
        """
        return next((idx for (idx, dt) in enumerate(
            lst) if dt["id"] == id), None)

    return [
        (
            # Stage info
            x,
            # Item drop type (Probability of dropping)
            # I'm sure there are better ways to do this but i'm a noob
            x["stageDropInfo"]["displayDetailRewards"][
                get_index(x["stageDropInfo"]["displayDetailRewards"])
            ]["dropType"],
        )
        for x in list(stage_list.values())
        # Check if item is in list
        if get_index(x["stageDropInfo"]["displayDetailRewards"]) is not None
    ]


building_data = None


def get_furniture(furniture: str) -> dict:
    """
    Grabs detailed furniture info (search by name or ID)

    Args:
        furniture (str): Furniture name or ID

    Returns:
        dict: A dict that contains furniture info with name or ID that matches the parameter
    """

    # Check if building_data is already loaded and load it from local file
    global building_data
    if building_data is None:
        with open("ArknightsData/en-US/gamedata/excel/building_data.json", "r") as f:
            building_data = json.load(f)

    # Get furniture list
    furniture_list = building_data["customData"]["furnitures"]
    return max(
        list(furniture_list.values()),
        # Match name or ID
        key=lambda x: max(ratio(x["name"], furniture),
                          ratio(x["id"], furniture)),
    )


enemy_handbook_table = None


def get_enemy(enemy: str) -> dict:
    """
    Grabs detailed enemy info (search by name or ID)

    Args:
        enemy (str): Enemy name or ID

    Returns:
        dict: A dict that contains enemy info with name or ID that matches the parameter
    """

    # Check if enemy_handbook_table is already loaded and load it from local
    # file
    global enemy_handbook_table
    if enemy_handbook_table is None:
        with open(
            "ArknightsData/en-US/gamedata/excel/enemy_handbook_table.json", "r"
        ) as f:
            enemy_handbook_table = json.load(f)

    return max(
        list(enemy_handbook_table.values()),
        # Match name or ID
        key=lambda x: max(ratio(x["name"], enemy), ratio(x["enemyId"], enemy)),
    )


tip_table = None


def get_tips(category: str) -> dict:
    """
    Grabs a random tip (with or without category)

    Args:
        category (str): Category of tip (optional) (must be correct)

    Returns:
        dict: A dict that contains tip about given category
    """

    # Check if tip_table is already loaded and load it from local file
    global tip_table
    if tip_table is None:
        with open("ArknightsData/en-US/gamedata/excel/tip_table.json", "r") as f:
            tip_table = json.load(f)

    # Get tip list
    tip_list = tip_table["tips"]

    # Random tip
    return random.choice(
        tip_list
        if category is None
        else [x for x in tip_list if x["category"] == category.upper()]
    )

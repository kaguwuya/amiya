"""
Store constant data
"""

import json
import sys

from inflection import underscore


def setup() -> None:
    """
    Assigns constants to module
    """

    # Load json data to gamedata_const
    gamedata_const = None
    with open("ArknightsData/en-US/gamedata/excel/gamedata_const.json", "r") as f:
        gamedata_const = json.load(f)

    # Assign variables to module
    for key, value in gamedata_const.items():
        setattr(
            sys.modules[__name__],
            underscore(key).upper(), # Following PEP8
            value)


# Item occurrence
OCCURRENCE = {
    "ALWAYS": "Fixed",
    "OFTEN": "Rare",
    "SOMETIMES": "Uncommon",
    "USUAL": "Chance Drop",
}

# Item drop probability
DROP_TYPE = {
    1: ["First Clear"],
    2: ["Fixed", "Rare"],
    3: ["Uncommon"],
    4: ["Chance Drop"],
    8: ["First Clear"],
}

# Profession table
# We need this as character_table.json doesn't show the profession as it is shown in-game
PROFESSION_TABLE = {
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

# Tag list for recruitment
TAG_LIST = [
    "Starter",
    "Senior Operator",
    "Top Operator",
    "Melee",
    "Ranged",
    "Guard",
    "Medic",
    "Vanguard",
    "Caster",
    "Sniper",
    "Defender",
    "Supporter",
    "Specialist",
    "Healing",
    "Support",
    "DPS",
    "AoE",
    "Slow",
    "Survival",
    "Defense",
    "Debuff",
    "Shift",
    "Crowd Control",
    "Nuker",
    "Summon",
    "Fast-Redeploy",
    "DP-Recovery",
    "Robot",
]

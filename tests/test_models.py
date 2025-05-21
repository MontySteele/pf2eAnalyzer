import pytest
from pydantic import ValidationError
from typing import List, Dict, Any, Optional # Ensure these are imported
import json # Added import

# Adjust the import path based on your project structure.
# If app.py is at the root, this should work.
# If GenericItem is moved, this will need to change.
from app import GenericItem, Build, BasePydanticModel, CharacterSheet # Ensure CharacterSheet is imported

# Test cases for GenericItem
def test_generic_item_all_fields():
    data = {
        "name": "Scroll of Healing",
        "qty": 3,
        "invested": True,
        "value": "15 gp",
        "bulk": "L",
        "location": "Backpack",
        "id": "ITEM_ID_SCROLL_HEAL",
        "img": "path/to/image.png",
        "data": {"skill": "Medicine"},
        "type": "consumable"
    }
    item = GenericItem(**data)
    assert item.name == "Scroll of Healing"
    assert item.qty == 3
    assert item.invested is True
    assert item.value == "15 gp"
    assert item.bulk == "L"
    assert item.location == "Backpack"
    assert item.id == "ITEM_ID_SCROLL_HEAL"
    assert item.img == "path/to/image.png"
    assert item.data == {"skill": "Medicine"}
    assert item.type == "consumable"

def test_generic_item_minimal_fields():
    data = {"name": "Dagger", "qty": 1}
    item = GenericItem(**data)
    assert item.name == "Dagger"
    assert item.qty == 1
    assert item.invested is False # Should default to False
    assert item.value is None
    assert item.bulk is None
    assert item.location is None
    assert item.id is None
    assert item.img is None
    assert item.data is None
    assert item.type is None

def test_generic_item_invested_true():
    data = {"name": "Magic Ring", "qty": 1, "invested": True}
    item = GenericItem(**data)
    assert item.invested is True

def test_generic_item_invested_false():
    data = {"name": "Basic Shield", "qty": 1, "invested": False}
    item = GenericItem(**data)
    assert item.invested is False

def test_generic_item_invested_absent():
    data = {"name": "Rope", "qty": 1} # invested is not provided
    item = GenericItem(**data)
    assert item.invested is False # Should default to False as per model definition

def test_generic_item_extra_fields():
    # GenericItem inherits from BasePydanticModel which should ignore extra fields
    data = {
        "name": "Mysterious Orb",
        "qty": 1,
        "color": "blue", # Extra field
        "origin": "unknown" # Extra field
    }
    try:
        item = GenericItem(**data)
        assert item.name == "Mysterious Orb"
        assert item.qty == 1
        assert not hasattr(item, 'color') # Extra fields should not be set on the model
    except ValidationError:
        pytest.fail("ValidationError was raised for extra fields, but BasePydanticModel should ignore them.")

# Placeholder for Build model tests - to be added in the next step
# This ensures the file is created correctly and pytest can find it.
def test_build_model_placeholder():
    assert True

# Minimal valid Build data for testing equipment (add other required fields for Build model)
# Based on app.py, Build requires: name, class (alias for class_name), level, ancestry,
# heritage, background, keyability, abilities, proficiencies, feats_raw (alias for feats),
# specials, money.
# We'll use placeholder values for these, focusing on the equipment.

MINIMAL_ABILITIES = {"str":10, "dex":10, "con":10, "int":10, "wis":10, "cha":10}
MINIMAL_MONEY = {"cp":0, "sp":0, "gp":0, "pp":0}
MINIMAL_PROFICIENCIES = {"classDC":0, "perception":0, "fortitude":0, "reflex":0, "will":0, "heavy":0, "medium":0, "light":0, "unarmored":0, "advanced":0, "martial":0, "simple":0, "unarmed":0, "castingArcane":0, "castingDivine":0, "castingOccult":0, "castingPrimal":0}

def test_build_model_with_various_equipment():
    build_data = {
        "name": "Test Character", "class": "Fighter", "level": 1,
        "ancestry": "Human", "heritage": "Versatile Human", "background": "Warrior",
        "keyability": "str", "abilities": MINIMAL_ABILITIES,
        "proficiencies": MINIMAL_PROFICIENCIES, "feats": [], "specials": [],
        "money": MINIMAL_MONEY,
        "equipment": [
            ["Sword", 1, "Not Really Invested"], # name, qty, invested_str (invested=False)
            ["Full Plate", 1, "worn_armor_container", "Invested"], # name, qty, location, invested_str (invested=True)
            ["Healing Potion", 5, "INVESTED"], # name, qty, invested_str (invested=True, case-insensitive)
            ["Rope", 1, "carried_container_id", "Stored"], # name, qty, location, invested_str (invested=False)
            ["Invalid Item Name Only"], # Invalid structure, should be skipped by validator
            ["Another Invalid Item", "not_a_qty", "Invested"] # Invalid qty, should be skipped by validator
        ]
    }
    build = Build(**build_data)
    
    # Expected number of items after validation (2 invalid items should be skipped)
    assert len(build.equipment) == 4 
    
    # Check Sword
    assert build.equipment[0].name == "Sword"
    assert build.equipment[0].qty == 1
    assert build.equipment[0].invested is False 
    assert build.equipment[0].location is None

    # Check Full Plate
    assert build.equipment[1].name == "Full Plate"
    assert build.equipment[1].qty == 1
    assert build.equipment[1].invested is True
    assert build.equipment[1].location == "worn_armor_container"

    # Check Healing Potion
    assert build.equipment[2].name == "Healing Potion"
    assert build.equipment[2].qty == 5
    assert build.equipment[2].invested is True # Validator should handle "INVESTED" case-insensitively
    assert build.equipment[2].location is None
    
    # Check Rope
    assert build.equipment[3].name == "Rope"
    assert build.equipment[3].qty == 1
    assert build.equipment[3].invested is False # "Stored" is not "Invested"
    assert build.equipment[3].location == "carried_container_id"

def test_build_model_with_empty_equipment():
    build_data = {
        "name": "Test Character Minimal", "class": "Wizard", "level": 1,
        "ancestry": "Elf", "heritage": "Ancient Elf", "background": "Scholar",
        "keyability": "int", "abilities": MINIMAL_ABILITIES,
        "proficiencies": MINIMAL_PROFICIENCIES, "feats": [], "specials": [],
        "money": MINIMAL_MONEY,
        "equipment": [] # Empty equipment list
    }
    build = Build(**build_data)
    assert len(build.equipment) == 0
    assert build.equipment == []

def test_build_model_equipment_field_absent():
    # This test checks if the equipment field correctly defaults to an empty list
    # if it's missing from the JSON, thanks to `default_factory=list`
    # and the validator returning [] for None input.
    build_data = {
        "name": "Test Character No Equip Field", "class": "Rogue", "level": 1,
        "ancestry": "Halfling", "heritage": "Cheeky Halfling", "background": "Criminal",
        "keyability": "dex", "abilities": MINIMAL_ABILITIES,
        "proficiencies": MINIMAL_PROFICIENCIES, "feats": [], "specials": [],
        "money": MINIMAL_MONEY
        # 'equipment' field is deliberately missing
    }
    build = Build(**build_data)
    assert build.equipment == [] # Should default to empty list

def test_parse_full_user_provided_jsons():
    user_json_string_arthur = """
    {"success":true,"build":{"name":"Arthur","class":"Champion","dualClass":null,"level":14,"ancestry":"Strix","heritage":"Duskwalker","background":"Chosen One","alignment":"N","gender":"Not set","age":"Not set","deity":"Not set","size":2,"sizeName":"Medium","keyability":"str","languages":["None selected"],"rituals":[],"resistances":[],"inventorMods":[],"abilities":{"str":20,"dex":12,"con":16,"int":10,"wis":18,"cha":16,"breakdown":{"ancestryFree":["Str"],"ancestryBoosts":["Dex"],"ancestryFlaws":[],"backgroundBoosts":["Str","Wis"],"classBoosts":["Str"],"mapLevelledBoosts":{"1":["Str","Con","Wis","Cha"],"5":["Str","Cha","Con","Wis"],"10":["Str","Cha","Con","Wis"]}}},"attributes":{"ancestryhp":8,"classhp":10,"bonushp":4,"bonushpPerLevel":1,"speed":25,"speedBonus":-5},"proficiencies":{"classDC":4,"perception":4,"fortitude":6,"reflex":4,"will":6,"heavy":6,"medium":6,"light":6,"unarmored":6,"advanced":0,"martial":6,"simple":6,"unarmed":6,"castingArcane":0,"castingDivine":4,"castingOccult":0,"castingPrimal":2,"acrobatics":0,"arcana":0,"athletics":4,"crafting":0,"deception":0,"diplomacy":6,"intimidation":0,"medicine":2,"nature":2,"occultism":0,"performance":0,"religion":6,"society":2,"stealth":2,"survival":2,"thievery":0},"mods":{"Acrobatics":{"Item Bonus":1},"Fortitude":{"Item Bonus":1},"Reflex":{"Item Bonus":1},"Will":{"Item Bonus":1}},"feats":[["Shield Block",null,"Awarded Feat",1],["Duskwalker",null,"Heritage",1,"Heritage Feat","standardChoice",null],["Defensive Advance",null,"Class Feat",1,"Champion Feat 1","standardChoice",null],["Fledgling Flight",null,"Ancestry Feat",1,"Strix Feat 1","standardChoice",null],["Pilgrim's Token",null,"Skill Feat",2,"Skill Feat 2","standardChoice",null],["Divine Grace",null,"Class Feat",2,"Champion Feat 2","standardChoice",null],["Cleric Dedication",null,"Archetype Feat",2,"Free Archetype 2","standardChoice",null],["Toughness",null,"General Feat",3,"General Feat 3","standardChoice",null],["Natural Medicine",null,"Skill Feat",4,"Skill Feat 4","standardChoice",null],["Aura of Courage",null,"Class Feat",4,"Champion Feat 4","standardChoice",null],["Basic Dogma",null,"Archetype Feat",4,"Free Archetype 4","parentChoice",null],["Domain Initiate",null,"Cleric Feat",4,"Basic DogmaFree Archetype 4","childChoice","Free Archetype 4"],["Ward Against Corruption",null,"Ancestry Feat",5,"Strix Feat 5","standardChoice",null],["Bon Mot",null,"Skill Feat",6,"Skill Feat 6","standardChoice",null],["Reactive Strike",null,"Class Feat",6,"Champion Feat 6","standardChoice",null],["Basic Cleric Spellcasting",null,"Archetype Feat",6,"Free Archetype 6","standardChoice",null],["Evangelize",null,"General Feat",7,"General Feat 7","standardChoice",null],["Student of the Canon",null,"Skill Feat",8,"Skill Feat 8","standardChoice",null],["Second Blessing",null,"Class Feat",8,"Champion Feat 8","standardChoice",null],["Divine Breadth",null,"Archetype Feat",8,"Free Archetype 8","standardChoice",null],["Strix Vengeance",null,"Ancestry Feat",9,"Strix Feat 9","standardChoice",null],["Break Curse",null,"Skill Feat",10,"Skill Feat 10","standardChoice",null],["Quick Shield Block",null,"Class Feat",10,"Champion Feat 10","standardChoice",null],["Advanced Dogma",null,"Archetype Feat",10,"Free Archetype 10","parentChoice",null],["Channel Smite",null,"Cleric Feat",10,"Advanced DogmaFree Archetype 10","childChoice","Free Archetype 10"],["Axuma's Vigor",null,"General Feat",11,"General Feat 11","standardChoice",null],["Battle Prayer",null,"Skill Feat",12,"Skill Feat 12","standardChoice",null],["Blessed Counterstrike",null,"Class Feat",12,"Champion Feat 12","standardChoice",null],["Expert Cleric Spellcasting",null,"Archetype Feat",12,"Free Archetype 12","standardChoice",null],["Ancestor's Transformation",null,"Ancestry Feat",13,"Strix Feat 13","standardChoice",null],["Lead Climber",null,"Skill Feat",14,"Skill Feat 14","standardChoice",null],["Divine Reflexes",null,"Class Feat",14,"Champion Feat 14","standardChoice",null],["Starlit Sentinel Dedication",null,"Archetype Feat",14,"Free Archetype 14","standardChoice",null]],"specials":["Deity Skill","Anathema","Sanctification","Deific Weapon","Champion's Aura","Justice Cause","Holy Aura","Retributive Strike","Lay on Hands","Low-Light Vision","Wings (Strix)","Prophecy's Pawn","Darkvision","Blessed Armament","Domain: Pain","Weapon Expertise","Armor Expertise","Weapon Specialization","Blessed Shield","Relentless Reaction","Champion Expertise","Reflex Expertise","Sacred Body","Exalted Reaction","Divine Will","Perception Expertise","Armor Mastery","Weapon Mastery","Starlit Transformation","Duskwalker"],"lores":[["Fortune-Telling",2]],"equipmentContainers":{},"equipment":[["Masquerade Scarf",1,"Invested"],["Bracelet of Dashing",1,"Invested"],["Hunter's Bane",3,"Invested"],["Snapleaf",3,"Invested"],["Vanishing Wayfinder",1,"Invested"],["Belt of Good Health",1,"Invested"],["Dragonscale Cameo",3,"Invested"],["Bracers of Devotion",1,"Invested"]],"specificProficiencies":{"trained":[],"expert":[],"master":[],"legendary":[]},"weapons":[{"name":"Skyrider Sword","qty":1,"prof":"simple","die":"d12","pot":3,"str":"greaterStriking","mat":null,"display":"+3 Weapon Striking (Greater) Flaming (Greater) Skyrider Sword","runes":["Flaming (Greater)"],"damageType":"S","attack":28,"damageBonus":8,"extraDamage":["1d6 Electricity","1d6 Fire"],"increasedDice":false,"isInventor":false},{"name":"Longsword","qty":1,"prof":"martial","die":"d8","pot":1,"str":"striking","mat":null,"display":"+1 Weapon Striking Deathdrinking Merciful Longsword","runes":["Deathdrinking","Merciful"],"damageType":"S","attack":26,"damageBonus":8,"extraDamage":[],"increasedDice":false,"isInventor":false},{"name":"Lucky Seven","qty":1,"prof":"martial","die":"d6","pot":3,"str":"majorStriking","mat":null,"display":"+3 Weapon Striking (Major) Impossible Vorpal Quickstrike Lucky Seven","runes":["Impossible","Vorpal","Quickstrike"],"damageType":"S","attack":28,"damageBonus":8,"extraDamage":[],"increasedDice":false,"isInventor":false}],"money":{"cp":0,"sp":0,"gp":1400,"pp":0},"armor":[{"name":"Full Plate","qty":1,"prof":"heavy","pot":2,"res":"resilient","mat":null,"display":"+2 Armor Resilient Size-Changing Winged Full Plate","worn":true,"runes":["Size-Changing","Winged"]},{"name":"Sturdy Shield (Minor)","qty":1,"prof":"shield","pot":0,"res":"","mat":null,"display":"","worn":true,"runes":[]}],"spellCasters":[{"name":"Archetype Cleric","magicTradition":"divine","spellcastingType":"prepared","ability":"wis","proficiency":4,"focusPoints":0,"innate":false,"perDay":[2,2,2,2,1,1,0,0,0,0,0],"spells":[{"spellLevel":0,"list":["Guidance","Divine Lance"]},{"spellLevel":1,"list":["Benediction","Harm"]},{"spellLevel":2,"list":["Spiritual Armament","Warrior's Regret"]},{"spellLevel":3,"list":["Warding Aggression","Warding Aggression"]},{"spellLevel":4,"list":["Dispelling Globe"]},{"spellLevel":5,"list":["Blink Charge"]}],"prepared":[],"blendedSpells":[]},{"name":"Ancestor's Transformation","magicTradition":"primal","spellcastingType":"prepared","ability":"cha","proficiency":2,"focusPoints":0,"innate":true,"perDay":[0,0,0,0,0,1,0,0,0,0,0],"spells":[{"spellLevel":0,"list":[]},{"spellLevel":1,"list":[]},{"spellLevel":2,"list":[]},{"spellLevel":3,"list":[]},{"spellLevel":4,"list":[]},{"spellLevel":5,"list":["Aerial Form"]}],"prepared":[],"blendedSpells":[]}],"focusPoints":2,"focus":{"divine":{"cha":{"abilityBonus":3,"proficiency":4,"itemBonus":0,"focusCantrips":[],"focusSpells":["Lay on Hands"]},"wis":{"abilityBonus":4,"proficiency":4,"itemBonus":0,"focusCantrips":[],"focusSpells":["Savor the Sting"]}}},"formula":[],"acTotal":{"acProfBonus":20,"acAbilityBonus":0,"acItemBonus":8,"acTotal":38,"shieldBonus":"2"},"pets":[],"familiars":[]}}
    """
    user_json_string_eunie = """
    {"success":true,"build":{"name":"Eunie","class":"Gunslinger","dualClass":null,"level":14,"ancestry":"Human","heritage":"Nephilim","background":"Field Medic","alignment":"N","gender":"Not set","age":"Not set","deity":"Not set","size":2,"sizeName":"Medium","keyability":"dex","languages":["None selected"],"rituals":[],"resistances":[],"inventorMods":[],"abilities":{"str":18,"dex":20,"con":18,"int":14,"wis":14,"cha":8,"breakdown":{"ancestryFree":[],"ancestryBoosts":[],"ancestryFlaws":[],"backgroundBoosts":[],"classBoosts":[],"mapLevelledBoosts":{"1":["Dex","Con","Str","Int"],"5":["Dex","Wis","Con","Str"],"10":["Dex","Wis","Con","Str"]}}},"attributes":{"ancestryhp":8,"classhp":8,"bonushp":0,"bonushpPerLevel":1,"speed":25,"speedBonus":5},"proficiencies":{"classDC":4,"perception":6,"fortitude":4,"reflex":6,"will":4,"heavy":0,"medium":4,"light":4,"unarmored":4,"advanced":0,"martial":6,"simple":6,"unarmed":6,"castingArcane":0,"castingDivine":0,"castingOccult":4,"castingPrimal":0,"acrobatics":2,"arcana":0,"athletics":0,"crafting":4,"deception":0,"diplomacy":0,"intimidation":0,"medicine":6,"nature":2,"occultism":6,"performance":0,"religion":0,"society":2,"stealth":2,"survival":2,"thievery":6},"mods":{"Reflex":{"Item Bonus":2},"Stealth":{"Item Bonus":2},"Thievery":{"Item Bonus":1},"Perception":{"Item Bonus":2},"Will":{"Item Bonus":2},"Occultism":{"Item Bonus":2},"Fortitude":{"Item Bonus":2}},"feats":[["Untrained Improvisation",null,"Awarded Feat",5],["Alchemical Crafting",null,"Awarded Feat",6],["Battle Medicine",null,"Awarded Feat",1],["Alchemical Crafting",null,"Awarded Feat",1],["Nephilim",null,"Heritage",1,"Heritage Feat","standardChoice",null],["Lawbringer",null,"Ancestry Feat",1,"Human Feat 1","standardChoice",null],["Munitions Crafter",null,"Class Feat",1,"Gunslinger Feat 1","standardChoice",null],["Dirty Trick",null,"Skill Feat",2,"Skill Feat 2","standardChoice",null],["Fake Out",null,"Class Feat",2,"Gunslinger Feat 2","standardChoice",null],["Witch Dedication",null,"Class Feat",2,"8d4f9b96-7c8c-46d5-aa48-e8e1a64eb097","standardChoice",null],["Ancestral Paragon",null,"General Feat",3,"General Feat 3","parentChoice",null],["Cooperative Nature",null,"Ancestry Feat",3,"Ancestral Paragon FeatGeneral Feat 3","childChoice","General Feat 3"],["Pickpocket",null,"Skill Feat",4,"Skill Feat 4","standardChoice",null],["Basic Witchcraft",null,"Class Feat",4,"Gunslinger Feat 4","parentChoice",null],["Basic Lesson",null,"Witch Feat",4,"ARCHETYPE_WITCH_Basic WitchcraftGunslinger Feat 4","childChoice","Gunslinger Feat 4"],["Basic Witch Spellcasting",null,"Class Feat",4,"d04cb493-853d-4ff4-9e09-570bde56341b","standardChoice",null],["Clever Improviser",null,"Ancestry Feat",5,"Human Feat 5","standardChoice",null],["Alchemist Dedication",null,"Class Feat",6,"76d9c081-db8b-4612-b698-e491fc0c9214","standardChoice",null],["Triggerbrand Salvo",null,"Class Feat",6,"Gunslinger Feat 6","standardChoice",null],["Cognitive Crossover",null,"Skill Feat",6,"Skill Feat 6","standardChoice",null],["Toughness",null,"General Feat",7,"General Feat 7","standardChoice",null],["Advanced Concoction",null,"Class Feat",8,"f51ec365-713f-41ce-8d18-ec523bd032ed","parentChoice",null],["Efficient Alchemy",null,"Alchemist Feat",8,"Advanced Discoveryf51ec365-713f-41ce-8d18-ec523bd032ed","childChoice","f51ec365-713f-41ce-8d18-ec523bd032ed"],["Basic Concoction",null,"Class Feat",8,"Gunslinger Feat 8","parentChoice",null],["Revivifying Mutagen",null,"Alchemist Feat",8,"Basic DiscoveryGunslinger Feat 8","childChoice","Gunslinger Feat 8"],["Consult the Spirits",null,"Skill Feat",8,"Skill Feat 8","standardChoice",null],["Divine Wings",null,"Ancestry Feat",9,"Human Feat 9","standardChoice",null],["Patron's Breadth",null,"Class Feat",10,"5df4bec1-0533-4463-aa48-98bd2957aa42","standardChoice",null],["Deflecting Shot",null,"Class Feat",10,"Gunslinger Feat 10","standardChoice",null],["Disturbing Knowledge",null,"Skill Feat",10,"Skill Feat 10","standardChoice",null],["Fleet",null,"General Feat",11,"General Feat 11","standardChoice",null],["Expert Witch Spellcasting",null,"Class Feat",12,"d4e94216-05cc-406b-bfe4-06db997ce30f","standardChoice",null],["Calm and Centered",null,"Skill Feat",12,"Skill Feat 12","standardChoice",null],["Voluminous Vials",null,"Class Feat",12,"Gunslinger Feat 12","standardChoice",null],["Cooperative Soul",null,"Ancestry Feat",13,"Human Feat 13","standardChoice",null],["Prepare Elemental Medicine",null,"Skill Feat",14,"Skill Feat 14","standardChoice",null],["Triggerbrand Blitz",null,"Class Feat",14,"Gunslinger Feat 14","standardChoice",null],["Advanced Witchcraft",null,"Class Feat",14,"f3d82aa9-4ff3-47f6-beb8-b001bc5aa503","parentChoice",null],["Greater Lesson",null,"Witch Feat",14,"ARCHETYPE_WITCH_Advanced Witchcraftf3d82aa9-4ff3-47f6-beb8-b001bc5aa503","childChoice","f3d82aa9-4ff3-47f6-beb8-b001bc5aa503"]],"specials":["Touch and Go","Way of the Triggerbrand","Slinger's Precision","Low-Light Vision","Spring the Trap","Spinner of Threads Patron","Stubborn","Lesson of Life","Gunslinger Weapon Mastery","Quick Alchemy","Perception Mastery","Weapon Specialization","Occultism","Gunslinger Expertise","Wind Them Up","Advanced Deed","Blast Dodger","Gunslinging Legend","Medium Armor Expertise","Lesson of the Flock","Nephilim"],"lores":[["Warfare",2]],"equipmentContainers":{"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52":{"containerName":"Sleeves of storage","bagOfHolding":true,"backpack":false}},"equipment":[["Alchemist's Toolkit",1,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Healer's Toolkit",1,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Bedroll",1,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Chalk",10,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Flint and Steel",1,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Rope",3,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Rations",2,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Torch",5,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Waterskin",1,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Soap",1,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Thieves' Toolkit",1,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Sleeves of Storage",1,"Invested"],["Quicksilver Mutagen (Moderate)",1,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Vanishing Wayfinder",1,"Invested"],["Aeon Stone (Western Star)",1,"Invested"],["Charlatan's Gloves",1,"Invested"],["Warding Tablets",1,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Spellstriker Staff",1,"Invested"],["Spyglass Eye",1,"a2340aeb-a07f-49a1-9ed9-2e6a6615bf52","Invested"],["Hexing Jar",1,"Invested"],["Obsidian Goggles (Greater)",1,"Invested"],["Staff of Healing (Major)",1,"Invested"]],"specificProficiencies":{"trained":[],"expert":[],"master":[],"legendary":["Piercing Wind - Melee","Piercing Wind - Ranged"]},"weapons":[{"name":"Piercing Wind - Melee","qty":1,"prof":"martial","die":"d6","pot":3,"str":"greaterStriking","mat":null,"display":"+3 Weapon Striking (Greater) Merciful Frost Keen Piercing Wind - Melee","runes":["Merciful","Frost","Keen"],"damageType":"S","attack":30,"damageBonus":8,"extraDamage":["1d6 Cold","1d4 Precision"],"increasedDice":false,"isInventor":false},{"name":"Piercing Wind - Ranged","qty":1,"prof":"martial","die":"d6","pot":3,"str":"greaterStriking","mat":null,"display":"+3 Weapon Striking (Greater) Merciful Frost Keen Piercing Wind - Ranged","runes":["Merciful","Frost","Keen"],"damageType":"P","attack":30,"damageBonus":3,"extraDamage":["1d6 Cold","1d6 precision"],"increasedDice":false,"isInventor":false}],"money":{"cp":0,"sp":3,"gp":338,"pp":0},"armor":[{"name":"Leather Armor","qty":1,"prof":"light","pot":2,"res":"greaterResilient","mat":null,"display":"+2 Armor Resilient (Greater) Invisibility (Greater) Shadow (Greater) Leather","worn":true,"runes":["Invisibility (Greater)","Shadow (Greater)"]}],"spellCasters":[{"name":"Archetype Witch","magicTradition":"occult","spellcastingType":"prepared","ability":"int","proficiency":4,"focusPoints":0,"innate":false,"perDay":[1,2,2,2,1,1,0,0,0,0,0],"spells":[{"spellLevel":0,"list":["Warp Step","Guidance"]},{"spellLevel":1,"list":["Heal","Sure Strike","Fleet Step","Endure"]},{"spellLevel":2,"list":["Dispel Magic","Status","See the Unseen"]},{"spellLevel":3,"list":["Heroism","Haste","Whirling Scarves","Wooden Double","Time Jump"]},{"spellLevel":4,"list":["Fly"]}],"prepared":[{"spellLevel":0,"list":["Guidance"]},{"spellLevel":1,"list":["Sure Strike","Sure Strike"]},{"spellLevel":2,"list":["Status","See the Unseen"]},{"spellLevel":3,"list":["Wooden Double","Time Jump"]},{"spellLevel":4,"list":["Endure"]},{"spellLevel":5,"list":["Blink Charge"]}],"blendedSpells":[]}],"focusPoints":2,"focus":{"occult":{"int":{"abilityBonus":2,"proficiency":4,"itemBonus":0,"focusCantrips":[],"focusSpells":["Life Boost","Sheltering Wings"]}}},"formula":[{"type":"Gunslinger Munitions Crafter","known":["Life Shot (Minor)","Numbing Tonic (Moderate)","Numbing Tonic (Greater)","Elixir of Life (Lesser)","Elixir of Life (Minor)","Elixir of Life (Greater)","Soothing Tonic (Greater)","Soothing Tonic (Moderate)","Elixir of Life (Moderate)","Life Shot (Moderate)"]},{"type":"Archetype Alchemist","known":["Numbing Tonic (Greater)","Silvertongue Mutagen (Greater)","Winterstep Elixir (Greater)","Astringent Venom","Quicksilver Mutagen (Greater)"]}],"acTotal":{"acProfBonus":18,"acAbilityBonus":4,"acItemBonus":3,"acTotal":35,"shieldBonus":null},"pets":[],"familiars":[{"type":"Familiar","name":"Familiar","equipment":[],"specific":null,"abilities":["Tough","Restorative Familiar","Partner in Crime"]}]}}
    """

    json_data_tuples = [
        (user_json_string_arthur, "Arthur"),
        (user_json_string_eunie, "Eunie")
    ]

    for json_str, char_name in json_data_tuples:
        try:
            data = json.loads(json_str)
            sheet = CharacterSheet(**data) # This is where the validator for equipment runs

            assert isinstance(sheet.build.equipment, list), f"Equipment for {char_name} is not a list."
            
            if sheet.build.equipment: # Only check first element if list is not empty
                assert isinstance(sheet.build.equipment[0], GenericItem), \
                    f"First equipment item for {char_name} is not a GenericItem instance."

            if char_name == "Arthur":
                assert sheet.build.name == "Arthur"
                masquerade_scarf = next((item for item in sheet.build.equipment if item.name == "Masquerade Scarf"), None)
                assert masquerade_scarf is not None, "Masquerade Scarf not found for Arthur"
                assert masquerade_scarf.qty == 1
                assert masquerade_scarf.invested is True # Validator should set this from "Invested"
                assert masquerade_scarf.location is None # Input ["Masquerade Scarf",1,"Invested"] has no explicit location

            elif char_name == "Eunie":
                assert sheet.build.name == "Eunie"
                alchemists_toolkit = next((item for item in sheet.build.equipment if item.name == "Alchemist's Toolkit"), None)
                assert alchemists_toolkit is not None, "Alchemist's Toolkit not found for Eunie"
                assert alchemists_toolkit.qty == 1
                assert alchemists_toolkit.invested is True # Validator should set this
                assert alchemists_toolkit.location == "a2340aeb-a07f-49a1-9ed9-2e6a6615bf52" # Validator should pick this up

                sleeves = next((item for item in sheet.build.equipment if item.name == "Sleeves of Storage"), None)
                assert sleeves is not None, "Sleeves of Storage not found for Eunie"
                assert sleeves.qty == 1
                assert sleeves.invested is True # Validator should set this
                assert sleeves.location is None # Input ["Sleeves of Storage",1,"Invested"] has no explicit location

        except ValidationError as e:
            pytest.fail(f"ValidationError for {char_name}: {e}")
        except Exception as e:
            pytest.fail(f"An unexpected error occurred for {char_name}: {e}")

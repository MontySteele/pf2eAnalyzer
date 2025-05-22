# pf2e_auditor_app.py

import streamlit as st
import json
from typing import List, Dict, Optional, Any, Union # Keep Union if used elsewhere
from pydantic import BaseModel, Field, validator
import google.generativeai as genai # NEW IMPORT

import json
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from urllib.parse import quote_plus # For AoN link generation
import hashlib # NEW IMPORT for hashing file content

# --- Pydantic Models ---

class Abilities(BaseModel):
    str_score: int = Field(alias='str')
    dex_score: int = Field(alias='dex')
    con_score: int = Field(alias='con')
    int_score: int = Field(alias='int')
    wis_score: int = Field(alias='wis')
    cha_score: int = Field(alias='cha')
    # Add breakdown if needed for more detailed analysis later

class Money(BaseModel):
    cp: int
    sp: int
    gp: int
    pp: int

    def total_in_gp(self) -> float:
        return self.pp * 10 + self.gp + self.sp / 10 + self.cp / 100

class Weapon(BaseModel):
    name: str
    qty: int
    prof: str
    die: str
    pot: Optional[int] = None # Potency rune level (+1, +2, +3)
    str_rune: Optional[str] = Field(default=None, alias='str') # Striking (striking, greaterStriking, majorStriking)
    mat: Optional[str] = None # Material
    display: str
    runes: List[str] = Field(default_factory=list) # Property runes
    damageType: str
    attack: Optional[int] = None
    damageBonus: Optional[int] = None
    extraDamage: List[str] = Field(default_factory=list)

class Armor(BaseModel):
    name: str
    qty: int
    prof: str
    pot: Optional[int] = None # Potency rune level
    res: Optional[str] = None # Resiliency rune (resilient, greaterResilient, majorResilient)
    mat: Optional[str] = None # Material
    display: str
    worn: bool
    runes: List[str] = Field(default_factory=list) # Property runes

class GenericItem(BasePydanticModel):
    name: str
    qty: int
    invested: Optional[bool] = False
    value: Optional[str] = None # e.g., "10 gp", "5 sp"
    bulk: Optional[str] = None  # e.g., "L", "1", "2"
    location: Optional[str] = None # Where the item is equipped or stored
    id: Optional[str] = None # Pathbuilder item ID
    img: Optional[str] = None # Image link for the item
    data: Optional[Dict[str, Any]] = None # For any other specific data
    type: Optional[str] = None # e.g. "item", "armor", "weapon"

# To handle the list-based feat structure:
class ProcessedFeat(BaseModel):
    name: Optional[str]
    category: str # "Awarded Feat", "Heritage", "Ancestry Feat", "Class Feat", etc.
    level_taken: int
    source_description: Optional[str] # e.g., "Fighter Feat 1", "Free Archetype 2"
    choice_type: Optional[str]
    parent_feat_id: Optional[str] = None # For childChoice feats

    # class Config:
    #     allow_population_by_field_name = True # Not needed if we parse manually

class BasePydanticModel(BaseModel):
    class Config:
        extra = 'ignore' # To prevent errors if Pathbuilder adds new fields

class SpellLevelEntry(BasePydanticModel):
    spellLevel: int
    list_of_spells: List[str] = Field(alias='list', default_factory=list)

class FocusAbilityDetails(BasePydanticModel): # For focus spells
    abilityBonus: int
    proficiency: int
    itemBonus: int
    focusCantrips: List[str] = Field(default_factory=list)
    focusSpells: List[str] = Field(default_factory=list)

class FocusTraditionDetails(BasePydanticModel): # For focus spells
    # This will hold fields like "cha", "wis" which are FocusAbilityDetails
    # We can use Dict[str, FocusAbilityDetails] to capture this dynamic nature
    # Or, if the ability keys are fixed (like just cha, wis, int etc.), define them explicitly
    cha: Optional[FocusAbilityDetails] = None
    wis: Optional[FocusAbilityDetails] = None
    con: Optional[FocusAbilityDetails] = None # Add others if they can appear
    str_score: Optional[FocusAbilityDetails] = Field(default=None, alias='str') # alias if 'str' is used
    dex: Optional[FocusAbilityDetails] = None
    int_score: Optional[FocusAbilityDetails] = Field(default=None, alias='int')


class FocusDetails(BasePydanticModel): # For the main 'focus' object
    divine: Optional[FocusTraditionDetails] = None
    arcane: Optional[FocusTraditionDetails] = None
    primal: Optional[FocusTraditionDetails] = None
    occult: Optional[FocusTraditionDetails] = None

class SpellCaster(BasePydanticModel):
    name: str
    magicTradition: str
    spellcastingType: str
    ability: str
    proficiency: int
    focusPoints: Optional[int] = Field(default=0) # This is from the top-level build.focusPoints
    innate: Optional[bool] = False
    perDay: List[int] = Field(default_factory=list)
    spells: List[SpellLevelEntry] = Field(default_factory=list)
    # 'prepared' and 'blendedSpells' are empty in this JSON, so default_factory=list is fine.
    # If they could contain data, model them more specifically.
    prepared: List[Any] = Field(default_factory=list) 
    blendedSpells: List[Any] = Field(default_factory=list)

class Build(BaseModel): # Add this to your existing Build model
    name: str
    class_name: str = Field(alias='class')
    level: int
    ancestry: str
    heritage: str
    background: str
    keyability: str
    abilities: Abilities
    proficiencies: Dict[str, int]
    feats_raw: List[List[Any]] = Field(alias='feats')
    processed_feats: List[ProcessedFeat] = Field(default_factory=list)
    specials: List[str]
    equipment: List[GenericItem] = Field(default_factory=list)
    weapons: List[Weapon] = Field(default_factory=list)
    money: Money
    armor: List[Armor] = Field(default_factory=list)
    spellCasters: List[SpellCaster] = Field(default_factory=list)
    focusPoints: Optional[int] = Field(default=0) # Top-level focus points
    focus: Optional[FocusDetails] = None # Add the new FocusDetails model here
    free_archetype_active: bool = False # NEW FIELD
    # acTotal: Dict[str, Any] # Can add if needed for AC checks

    @validator('equipment', pre=True, always=True)
    def transform_equipment_list(cls, v):
        if not v: # Handles None or empty list
            return [] 
        if not isinstance(v, list):
            # Optionally, log a warning or raise ValueError if the type is unexpected.
            # For now, returning an empty list to prevent downstream errors.
            print(f"Warning: Expected a list for equipment, got {type(v)}. Returning empty list.")
            return []

        processed_list = []
        for item_data in v:
            if isinstance(item_data, list):
                name: Optional[str] = None
                qty: Optional[int] = None
                location: Optional[str] = None
                invested: bool = False # Default to False

                if not item_data: # Skip empty lists
                    continue

                name = str(item_data[0]) # Name is always first

                if len(item_data) == 3:
                    # Format: [name, qty, invested_str_or_container_id]
                    # Pathbuilder seems to sometimes put container_id here if not invested.
                    # For this case, we assume item_data[2] is primarily for 'invested' status.
                    try:
                        qty = int(item_data[1])
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse qty '{item_data[1]}' for item '{name}'. Skipping item.")
                        continue 
                    
                    # Check if the third element is "Invested"
                    # If not, it could be a location or just some other non-invested string.
                    # Based on examples, "Invested" is key.
                    # If it's not "Invested", we assume not invested and no specific location from this element.
                    if isinstance(item_data[2], str) and item_data[2].lower() == "invested":
                        invested = True
                    # If item_data[2] is a container_id (looks like a UUID or similar), 
                    # it's not "Invested", so invested remains False. Location is not set here.

                elif len(item_data) == 4:
                    # Format: [name, qty, container_id_str, invested_str]
                    try:
                        qty = int(item_data[1])
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse qty '{item_data[1]}' for item '{name}'. Skipping item.")
                        continue
                    
                    # Third element is location if it's a string and doesn't look like "Invested"
                    if isinstance(item_data[2], str) and item_data[2].lower() != "invested":
                        location = str(item_data[2])
                    
                    # Fourth element is for invested status
                    if isinstance(item_data[3], str) and item_data[3].lower() == "invested":
                        invested = True
                    
                elif len(item_data) == 2: # Example: ["Dagger", 1]
                    try:
                        qty = int(item_data[1])
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse qty '{item_data[1]}' for item '{name}'. Skipping item.")
                        continue
                    # invested remains False, location remains None
                
                else:
                    # Invalid format for list item, skip or log
                    print(f"Warning: Unexpected item_data format for '{name}': {item_data}. Skipping item.")
                    continue

                if name is not None and qty is not None:
                    processed_list.append({
                        "name": name,
                        "qty": qty,
                        "invested": invested,
                        "location": location
                        # Other GenericItem fields (value, bulk, id, img, data, type)
                        # will default to None or their Pydantic defaults.
                    })
            elif isinstance(item_data, dict):
                # If some items are already dicts, assume they are correctly structured for GenericItem
                # or will be handled by GenericItem's own parsing.
                # For robustness, ensure 'name' and 'qty' are present if possible, or let GenericItem validate.
                processed_list.append(item_data)
            else:
                # Unknown item format, skip or log
                print(f"Warning: Unknown equipment item format: {item_data}. Skipping item.")
                continue
        
        return processed_list

    @validator('processed_feats', pre=False, always=True)
    def process_the_feats(cls, v, values):
        # ... (existing validator logic for processing feats_raw) ...
        # (No changes needed here, just ensure it's present)
        if v: return v # Already populated
        raw_feats = values.get('feats_raw', [])
        parsed_list = []
        for feat_data in raw_feats:
            try:
                name = feat_data[0] if len(feat_data) > 0 else None
                category = feat_data[2] if len(feat_data) > 2 else "Unknown Feat Type"
                level_taken = feat_data[3] if len(feat_data) > 3 else 0
                source_desc = feat_data[4] if len(feat_data) > 4 else None
                choice_type = feat_data[5] if len(feat_data) > 5 else None
                parent_id = feat_data[6] if len(feat_data) > 6 else None
                if name:
                    parsed_list.append(
                        ProcessedFeat(
                            name=name, category=category, level_taken=level_taken,
                            source_description=source_desc, choice_type=choice_type,
                            parent_feat_id=parent_id))
            except IndexError: print(f"Warning: Could not parse feat_data: {feat_data}")
            except Exception as e: print(f"Warning: Error parsing feat_data {feat_data}: {e}")
        return parsed_list


    @validator('free_archetype_active', pre=False, always=True) # NEW VALIDATOR
    def set_free_archetype_status(cls, v, values):
        # This validator runs after 'processed_feats' should be populated
        processed_feats_list = values.get('processed_feats', [])
        return is_free_archetype_active_from_feats(processed_feats_list)

class CharacterSheet(BaseModel):
    success: bool
    build: Build

# --- Analysis/Checks ---

def is_free_archetype_active_from_feats(processed_feats: List[ProcessedFeat]) -> bool:
    for feat in processed_feats:
        if feat.source_description and "Free Archetype" in feat.source_description:
            return True
    return False

def check_unspent_gold(character: CharacterSheet, gold_threshold_factor: int = 50) -> List[str]:
    suggestions = []
    total_gp = character.build.money.total_in_gp()
    level = character.build.level
    threshold = level * gold_threshold_factor

    if total_gp > threshold:
        suggestions.append(
            f"High Unspent Gold: Character has {total_gp:.2f}gp. "
            f"Consider spending some; a guideline for this level might be less than {threshold}gp unspent. "
            f"Look into consumables, gear upgrades, or savings for a major purchase."
        )
    if total_gp < level * 5 and level > 1: # Arbitrary low gold threshold
         suggestions.append(
            f"Low Gold: Character has only {total_gp:.2f}gp. This might be tight for consumables or repairs."
        )
    return suggestions

def get_rune_recommendations(level: int) -> Dict[str, Any]:
    """Returns recommended potency/striking/resiliency levels for a character level."""
    recs = {
        "weapon_potency": 0, "weapon_striking": None, "weapon_striking_name": "None",
        "armor_potency": 0, "armor_resiliency": None, "armor_resiliency_name": "None"
    }
    # Weapon Potency
    if level >= 16: recs["weapon_potency"] = 3
    elif level >= 10: recs["weapon_potency"] = 2
    elif level >= 2: recs["weapon_potency"] = 1
    # Weapon Striking
    if level >= 19: recs["weapon_striking"], recs["weapon_striking_name"] = "majorStriking", "Major Striking"
    elif level >= 12: recs["weapon_striking"], recs["weapon_striking_name"] = "greaterStriking", "Greater Striking"
    elif level >= 4: recs["weapon_striking"], recs["weapon_striking_name"] = "striking", "Striking"
    # Armor Potency
    if level >= 18: recs["armor_potency"] = 3
    elif level >= 11: recs["armor_potency"] = 2
    elif level >= 5: recs["armor_potency"] = 1
    # Armor Resiliency
    if level >= 20: recs["armor_resiliency"], recs["armor_resiliency_name"] = "majorResilient", "Major Resilient"
    elif level >= 14: recs["armor_resiliency"], recs["armor_resiliency_name"] = "greaterResilient", "Greater Resilient"
    elif level >= 8: recs["armor_resiliency"], recs["armor_resiliency_name"] = "resilient", "Resilient"
    return recs

def check_equipment_runes(character: CharacterSheet) -> List[str]:
    suggestions = []
    level = character.build.level
    recommendations = get_rune_recommendations(level)

    # Weapon Checks
    for weapon in character.build.weapons:
        # Potency Rune
        if weapon.pot is None or weapon.pot < 1:
            suggestions.append(f"Weapon '{weapon.name}': Missing Potency rune. Recommended: +{recommendations['weapon_potency']}")
        elif weapon.pot < recommendations["weapon_potency"]:
            suggestions.append(
                f"Weapon '{weapon.name}': Potency rune (+{weapon.pot}) is lower than recommended (+{recommendations['weapon_potency']}) for level {level}."
            )

        # Striking Rune (only if potency is present)
        if weapon.pot and weapon.pot > 0: # Potency rune is a prerequisite for striking
            if not weapon.str_rune:
                suggestions.append(f"Weapon '{weapon.name}': Missing Striking rune. Recommended: {recommendations['weapon_striking_name']}")
            else:
                # Simplistic comparison for striking runes
                current_striking_level = {"striking": 1, "greaterStriking": 2, "majorStriking": 3}.get(weapon.str_rune, 0)
                recommended_striking_level = {"striking": 1, "greaterStriking": 2, "majorStriking": 3}.get(recommendations["weapon_striking"], 0)
                if current_striking_level < recommended_striking_level:
                     suggestions.append(
                        f"Weapon '{weapon.name}': Striking rune ({weapon.str_rune}) is lower than recommended ({recommendations['weapon_striking_name']}) for level {level}."
                    )

        # Property Runes
        if weapon.pot and weapon.pot > 0:
            max_property_runes = weapon.pot
            if len(weapon.runes) < max_property_runes:
                suggestions.append(
                    f"Weapon '{weapon.name}': Has {len(weapon.runes)}/{max_property_runes} property rune slots filled. Consider adding more."
                )

    # Armor Checks (only for worn armor)
    for armor_item in character.build.armor:
        if armor_item.worn:
            # Potency Rune
            if armor_item.pot is None or armor_item.pot < 1:
                suggestions.append(f"Armor '{armor_item.name}': Missing Potency rune. Recommended: +{recommendations['armor_potency']}")
            elif armor_item.pot < recommendations["armor_potency"]:
                suggestions.append(
                    f"Armor '{armor_item.name}': Potency rune (+{armor_item.pot}) is lower than recommended (+{recommendations['armor_potency']}) for level {level}."
                )

            # Resiliency Rune (only if potency is present)
            if armor_item.pot and armor_item.pot > 0:
                if not armor_item.res:
                    suggestions.append(f"Armor '{armor_item.name}': Missing Resiliency rune. Recommended: {recommendations['armor_resiliency_name']}")
                else:
                    current_resiliency_level = {"resilient": 1, "greaterResilient": 2, "majorResilient": 3}.get(armor_item.res, 0)
                    recommended_resiliency_level = {"resilient": 1, "greaterResilient": 2, "majorResilient": 3}.get(recommendations["armor_resiliency"], 0)
                    if current_resiliency_level < recommended_resiliency_level:
                        suggestions.append(
                            f"Armor '{armor_item.name}': Resiliency rune ({armor_item.res}) is lower than recommended ({recommendations['armor_resiliency_name']}) for level {level}."
                        )
            # Property Runes
            if armor_item.pot and armor_item.pot > 0:
                max_property_runes = armor_item.pot
                if len(armor_item.runes) < max_property_runes:
                    suggestions.append(
                        f"Armor '{armor_item.name}': Has {len(armor_item.runes)}/{max_property_runes} property rune slots filled. Consider adding more."
                    )
    return suggestions

def check_missing_feat_slots(character: CharacterSheet) -> List[str]:
    suggestions = []
    level = character.build.level
    feats = character.build.processed_feats
    char_class = character.build.class_name.lower()
    is_fa_active = character.build.free_archetype_active # Use the new field

    # 1. Check for explicit "Unselected", "Choose", or "Empty" feat names from Pathbuilder
    # These are strong indicators of an unfilled slot.
    unselected_placeholders = []
    for f in feats:
        if f.name and (
            "unselected" in f.name.lower() or \
            "choose" in f.name.lower() or \
            "empty" in f.name.lower() or \
            f.name.strip() == "" or \
            (f.category and "unselected" in f.category.lower()) # Sometimes category might indicate it
            ):
            # Try to get a more descriptive source for the unselected feat
            source_info = f.source_description if f.source_description else f.category
            unselected_placeholders.append(f"{f.name} (slot: {source_info}, level {f.level_taken})")

    if unselected_placeholders:
        suggestions.append(
            f"Unselected Feat Slots Found: Pathbuilder indicates potentially empty slots for: {'; '.join(unselected_placeholders)}. Please select feats for these slots."
        )

    # 2. Count expected vs. actual feats (as a secondary check)
    # This section is more for auditing if Pathbuilder missed something or for general understanding.
    # Pathbuilder is usually quite good at enforcing feat slot rules.

    # Expected counts
    expected_ancestry_feats = sum(1 for lvl_req in [1, 5, 9, 13, 17] if level >= lvl_req)
    
    expected_skill_feats_from_level = level // 2
    if char_class == "rogue": # Rogues get a skill feat every level
        expected_skill_feats = level
    # elif char_class == "investigator": # Investigators also get more
    #    expected_skill_feats = level # (and other similar classes)
    else:
        expected_skill_feats = expected_skill_feats_from_level
    # Note: Bonus skill feats from high Intelligence are hard to calculate here without Ability Scores fully parsed
    # and applied to rules. Pathbuilder handles this, so placeholder check is more important.

    expected_general_feats = sum(1 for lvl_req in [3, 7, 11, 15, 19] if level >= lvl_req)
    
    expected_class_feats = 0
    if level >= 1:
        expected_class_feats = 1 + (level // 2) # L1, L2, L4, L6...
    if char_class == "fighter" and level >= 1:
        expected_class_feats += 1 # Fighters get an extra class feat at L1

    expected_archetype_feats = 0
    if is_fa_active and level >= 2:
        expected_archetype_feats = level // 2 # Archetype feat at L2, L4, L6...

    # Actual counts from Pathbuilder's list
    actual_ancestry_feats = sum(1 for f in feats if f.category == "Ancestry Feat" or (f.category == "Heritage" and f.source_description and "Feat" in f.source_description))
    actual_skill_feats = sum(1 for f in feats if f.category == "Skill Feat") # Assumes background/awarded skill feats are fine.
    actual_general_feats = sum(1 for f in feats if f.category == "General Feat")
    actual_class_feats = sum(1 for f in feats if f.category == "Class Feat")
    actual_archetype_feats = sum(1 for f in feats if f.category == "Archetype Feat")

    # Reporting discrepancies (usually only if no placeholders found, as placeholders are more direct)
    if not unselected_placeholders:
        if actual_ancestry_feats < expected_ancestry_feats:
            suggestions.append(f"Ancestry Feats Count: Expected {expected_ancestry_feats}, found {actual_ancestry_feats}. Review ancestry feat progression (Levels 1, 5, 9, 13, 17).")
        
        # Skill feat count is very complex due to Int/class bonuses that Pathbuilder handles.
        # The placeholder check is usually sufficient. This count is a very rough guide.
        # if actual_skill_feats < expected_skill_feats:
        #     suggestions.append(f"Skill Feats Count: Expected ~{expected_skill_feats} (base), found {actual_skill_feats}. Pathbuilder usually handles this with placeholders if a slot is empty.")

        if actual_general_feats < expected_general_feats:
            suggestions.append(f"General Feats Count: Expected {expected_general_feats}, found {actual_general_feats}. Review general feat progression (Levels 3, 7, 11, 15, 19).")
        
        # Class feat counting also has nuances (e.g. Ancient Elf). Pathbuilder placeholders are key.
        if actual_class_feats < expected_class_feats:
             suggestions.append(f"Class Feats Count: Expected {expected_class_feats} (for {char_class}), found {actual_class_feats}. Review class feat progression.")

        if is_fa_active and actual_archetype_feats < expected_archetype_feats:
            suggestions.append(f"Free Archetype Feats Count: Expected {expected_archetype_feats}, found {actual_archetype_feats}. Review archetype feat progression for Free Archetype slots (Levels 2, 4, 6...).")
        elif not is_fa_active and actual_archetype_feats > 0:
             suggestions.append(f"Archetype Feats Present: Found {actual_archetype_feats} Archetype feats, but Free Archetype variant rule does not seem to be active (no feats sourced from 'Free Archetype X'). These feats should be taking up Class Feat slots if selected via multiclass archetypes.")


    return suggestions

def check_constitution_score(character: CharacterSheet) -> List[str]:
    suggestions = []
    score = character.build.abilities.con_score

    if score < 10:
        suggestions.append(
            f"Critically Low Constitution (CON): Your CON score of {score} is very low. "
            f"This will result in dangerously low Hit Points, making you highly susceptible "
            f"to being knocked out or killed. Consider increasing this score as a high priority."
        )
    elif score < 12: # This means score is 10 or 11
        suggestions.append(
            f"Low Constitution (CON): Your CON score of {score} is a bit low. "
            f"This can lead to lower than average Hit Points, impacting your survivability. "
            f"Consider if this is a conscious choice for your character build."
        )
    # No suggestion if score is 12 or higher
        return suggestions
    
def check_basic_consumables(character: CharacterSheet) -> List[str]:
    """
    Checks if a character above level 1 has any healing potions.
    """
    suggestions = []
    level = character.build.level
    equipment = character.build.equipment

    if level <= 1:
        return suggestions # No suggestion for level 1 characters

    has_healing_potion = False
    for item in equipment:
        if isinstance(item, dict) and "name" in item:
            item_name = item.get("name", "")
            if isinstance(item_name, str) and "healing potion" in item_name.lower():
                has_healing_potion = True
                break # Found one, no need to check further

    if not has_healing_potion:
        suggestions.append(
            "Character is above level 1 and has no healing potions. Consider acquiring some for survivability."
        )

# --- UPDATED AoN Link Function ---
def get_aon_link(item_name: str, item_type: Optional[str] = None) -> str:
    """Generates a search link to Archives of Nethys for a given item name."""
    # Basic sanitization and URL encoding
    query = quote_plus(item_name.strip())
    # We can try to be a bit smarter with the item_type later if needed,
    # but a general search is usually quite good on AoN.
    # Example: https://2e.aonprd.com/Search.aspx?q=Sudden%20Charge
    return f"https://2e.aonprd.com/Search.aspx?q={query}"

# --- LLM Function for Combat Suggestions (from previous step, ensure it's here) ---
@st.cache_data(ttl=3600) # Cache for 1 hour
def get_llm_combat_suggestions_cached(file_content_hash: str, _character_data_dict: dict, google_api_key: str, llm_model_name: str = "gemini-1.5-flash-latest") -> List[str]:
    """
    Generates combat suggestions using a Google Gemini LLM, with caching.
    Assumes Pydantic models are correctly defined for _character_data_dict parsing.
    """
    # The file_content_hash argument is used by Streamlit to determine if the input has changed.
    
    try:
        # This is where your Pydantic models parse the input dictionary
        character = CharacterSheet(**_character_data_dict)
    except Exception as e:
        # Cannot use st.error directly in cached function for UI. Log or return error string.
        print(f"Pydantic Parsing Error (Combat Suggestions): {e}")
        return [f"Error parsing character data in cached function: {e}"]

    if not google_api_key:
        return ["Google AI Studio API key not provided. Cannot fetch LLM suggestions."]
    
    try:
        genai.configure(api_key=google_api_key)
    except Exception as e:
        print(f"Error configuring Google AI SDK (Combat Suggestions): {e}")
        return [f"Error configuring Google AI SDK: {e}"]
        
    model = genai.GenerativeModel(model_name=llm_model_name)
    build = character.build # build is an instance of your Pydantic 'Build' model

    # --- Prompt Construction ---
    prompt_lines = [
        "You are an expert Pathfinder 2nd Edition tactical advisor. A player needs suggestions for their turn in combat.",
        f"Character Name: {build.name}",
        f"Class: {build.class_name}, Level: {build.level}",
        f"Key Ability Score for class features/spells: {build.keyability.upper()}",
        f"Ancestry: {build.ancestry}, Heritage: {build.heritage}",
        "\nRelevant Feats:",
        # Ensure build.processed_feats contains Pydantic ProcessedFeat objects
        *[f"- {feat.name}" for feat in build.processed_feats if feat.name and feat.level_taken <= build.level and "unselected" not in feat.name.lower()],
        "\nNotable Special Abilities/Class Features:",
        *[f"- {special}" for special in build.specials],
    ]

    if build.weapons:
        prompt_lines.append("\nEquipped Weapons:")
        for weapon in build.weapons: # weapon is Pydantic Weapon model
            prompt_lines.append(f"- {weapon.display} (Damage: {weapon.die}{''.join([f' +{ed}' for ed in weapon.extraDamage]) if weapon.extraDamage else ''})")
    
    if build.armor:
        worn_armor = next((arm for arm in build.armor if arm.worn), None) # arm is Pydantic Armor model
        if worn_armor:
            prompt_lines.append(f"\nWorn Armor: {worn_armor.display}")

    # Spellcasting Information
    if build.spellCasters: # build.spellCasters is List[Pydantic_SpellCaster_Model]
        for sc in build.spellCasters: # sc is Pydantic SpellCaster model
            innate_note = " (Innate)" if sc.innate else ""
            prompt_lines.append(f"\nSpellcasting ({sc.name}{innate_note} - Tradition: {sc.magicTradition}, Type: {sc.spellcastingType}, Ability: {sc.ability.upper()}):")

            # Spell Slots per Day
            if sc.perDay:
                slot_strings = []
                for i, num_slots in enumerate(sc.perDay): # i is spell level (0-indexed)
                    if num_slots > 0:
                        slot_strings.append(f"L{i}: {num_slots}")
                if slot_strings:
                    prompt_lines.append(f"  Spell Slots per Day: {', '.join(slot_strings)}")
            
            # Focus Spells (using the new Pydantic structure for build.focus)
            all_focus_spells_for_prompt = []
            if build.focus: # build.focus is Pydantic FocusDetails model
                # Iterate through traditions (divine, arcane, etc.)
                for _tradition_name, tradition_details in build.focus.dict(exclude_none=True).items():
                    if isinstance(tradition_details, dict):
                        # Iterate through abilities (cha, wis, etc.) within the tradition
                        for _ability_name, ability_details_dict in tradition_details.items():
                            if isinstance(ability_details_dict, dict) and 'focusSpells' in ability_details_dict:
                                spells_from_focus = ability_details_dict.get('focusSpells', [])
                                if isinstance(spells_from_focus, list):
                                    all_focus_spells_for_prompt.extend(fs_name for fs_name in spells_from_focus if isinstance(fs_name, str) and fs_name.strip())
            
            if all_focus_spells_for_prompt:
                unique_focus_spells = sorted(list(set(all_focus_spells_for_prompt)))
                prompt_lines.append("  Focus Spells: " + ", ".join(unique_focus_spells))

            # Regular Spells (Prepared/Known)
            has_listed_regular_spells = False
            if sc.spells: # sc.spells is List[Pydantic_SpellLevelEntry_Model]
                for spell_level_obj in sc.spells: # spell_level_obj is Pydantic SpellLevelEntry
                    # spell_level_obj.list_of_spells is List[str] due to Field(alias='list')
                    valid_spell_names = [s_name for s_name in spell_level_obj.list_of_spells 
                                         if isinstance(s_name, str) and s_name.strip() and "unselected" not in s_name.lower()]
                    if valid_spell_names:
                        has_listed_regular_spells = True
                        prompt_lines.append(f"  Level {spell_level_obj.spellLevel} Spells: " + ", ".join(valid_spell_names))
            
            if not has_listed_regular_spells and not all_focus_spells_for_prompt:
                prompt_lines.append("  (No specific regular or focus spells found in this caster's data).")

    prompt_lines.extend([
        "\nBased on this character, provide 3-5 distinct and actionable combat suggestions for a typical combat encounter.",
        "Each suggestion should be a paragraph explaining the action(s), why it's effective for this character (referencing specific feats, spells, or abilities), and the general tactical benefit.",
        "Prioritize creative uses of their abilities and synergies. Format each suggestion clearly, perhaps starting each with 'Suggestion:' or using markdown for structure."
    ])
    
    full_prompt = "\n".join(prompt_lines)
    # st.session_state is UI specific, if this function is purely backend, consider returning prompt too
    if 'st' in globals() and hasattr(st, 'session_state'): # Check if Streamlit context exists
        st.session_state.last_llm_prompt = full_prompt 

    try:
        generation_config = genai.types.GenerationConfig(max_output_tokens=20000) # Ensure enough tokens for detailed response
        response = model.generate_content(full_prompt, generation_config=generation_config)
        response_content = response.text
        
        # Suggestion Parsing Logic (remains the same)
        split_markers = ["Suggestion:", "\n\n**", "\n\n*", "\n\n-", "\n\n1.", "\n\n2.", "\n\n3.", "\n\n4.", "\n\n5."]
        current_best_split = [response_content] # Default to whole content if no markers found
        for marker in split_markers:
            if marker in response_content:
                potential_split = [s.strip() for s in response_content.split(marker) if s.strip()]
                if not potential_split: continue

                # If the marker itself isn't the suggestion text (e.g. "Suggestion:"),
                # we might need to prepend it to all but the first (if it was a numbered/bulleted list from LLM)
                # For "Suggestion:", the first part of split is empty or preamble, so we take the rest.
                if marker == "Suggestion:":
                     current_best_split = potential_split # Each item after "Suggestion:" is a suggestion
                elif marker.strip().endswith((".", "-", "*")): # For list-like markers
                     current_best_split = [potential_split[0]] + [marker.strip() + " " + s for s in potential_split[1:]]
                else: # For "**" or other section markers
                    current_best_split = potential_split
                break # Take the first marker that successfully splits into multiple parts

        return current_best_split if any(s.strip() for s in current_best_split) else ["LLM returned no distinct suggestions or format was unexpected."]

    except Exception as e:
        print(f"Error calling Google Generative AI (Combat Suggestions): {e}")
        # Consider checking response.prompt_feedback for safety blocks by the API
        # if 'response' in locals() and hasattr(response, 'prompt_feedback'):
        # print(f"Prompt Feedback: {response.prompt_feedback}")
        return [f"Error calling Google Generative AI: {e}"]


@st.cache_data(ttl=3600) # Cache for 1 hour
def get_llm_character_qa_answer_cached(file_content_hash: str, _character_data_dict: dict, user_question: str, google_api_key: str, llm_model_name: str = "gemini-1.5-flash-latest") -> str:
    """
    Generates an answer to a user's question about their character using a Google Gemini LLM, with caching.
    Assumes Pydantic models are correctly defined for _character_data_dict parsing.
    """
    try:
        character = CharacterSheet(**_character_data_dict)
    except Exception as e:
        print(f"Pydantic Parsing Error (Q&A): {e}")
        return f"Error re-parsing character data in cached Q&A function: {e}"

    if not google_api_key:
        return "Google AI Studio API key not provided. Cannot answer question."
    if not user_question:
        return "No question asked."

    try:
        genai.configure(api_key=google_api_key)
    except Exception as e:
        print(f"Error configuring Google AI SDK (Q&A): {e}")
        return f"Error configuring Google AI SDK: {e}"

    model = genai.GenerativeModel(model_name=llm_model_name)
    build = character.build # build is an instance of your Pydantic 'Build' model

    # --- Prompt Construction ---
    context_lines = [
        "You are a helpful Pathfinder 2nd Edition expert assistant. You will be given information about a player character and a question from the user about that character. Answer the question based *only* on the provided character information and general Pathfinder 2e rules.",
        "Do not invent new abilities or information not present in the character sheet summary. If the information is not in the sheet, state that.",
        "\n--- Character Information ---",
        f"Name: {build.name}, Class: {build.class_name}, Level: {build.level}",
        f"Key Ability: {build.keyability.upper()}",
        "Feats: " + ", ".join([feat.name for feat in build.processed_feats if feat.name and "unselected" not in feat.name.lower()]),
        "Special Abilities: " + ", ".join(build.specials),
    ]

    if build.weapons:
        context_lines.append("Weapons: " + ", ".join([w.display for w in build.weapons]))
    
    if build.armor:
        worn_armor_item = next((a for a in build.armor if a.worn), None)
        if worn_armor_item:
            context_lines.append("Worn Armor: " + worn_armor_item.display)
    
    # Spellcasting Information (Mirrors the logic from combat suggestions)
    if build.spellCasters:
        for sc in build.spellCasters:
            innate_note = " (Innate)" if sc.innate else ""
            context_lines.append(f"\nSpellcasting ({sc.name}{innate_note} - Tradition: {sc.magicTradition}, Type: {sc.spellcastingType}, Ability: {sc.ability.upper()}):")
            if sc.perDay:
                slot_strings = []
                for i, num_slots in enumerate(sc.perDay):
                    if num_slots > 0: slot_strings.append(f"L{i}: {num_slots}")
                if slot_strings: context_lines.append(f"  Spell Slots per Day: {', '.join(slot_strings)}")
            
            all_focus_spells_for_prompt = []
            if build.focus:
                for _tradition_name, tradition_details in build.focus.dict(exclude_none=True).items():
                    if isinstance(tradition_details, dict):
                        for _ability_name, ability_details_dict in tradition_details.items():
                            if isinstance(ability_details_dict, dict) and 'focusSpells' in ability_details_dict:
                                spells_from_focus = ability_details_dict.get('focusSpells', [])
                                if isinstance(spells_from_focus, list):
                                    all_focus_spells_for_prompt.extend(fs_name for fs_name in spells_from_focus if isinstance(fs_name, str) and fs_name.strip())
            if all_focus_spells_for_prompt:
                unique_focus_spells = sorted(list(set(all_focus_spells_for_prompt)))
                context_lines.append("  Focus Spells: " + ", ".join(unique_focus_spells))

            has_listed_regular_spells = False
            if sc.spells:
                for spell_level_obj in sc.spells:
                    valid_spell_names = [s_name for s_name in spell_level_obj.list_of_spells 
                                         if isinstance(s_name, str) and s_name.strip() and "unselected" not in s_name.lower()]
                    if valid_spell_names:
                        has_listed_regular_spells = True
                        context_lines.append(f"  Level {spell_level_obj.spellLevel} Spells: " + ", ".join(valid_spell_names))
            if not has_listed_regular_spells and not all_focus_spells_for_prompt:
                context_lines.append("  (No specific regular or focus spells found in this caster's data).")

    context_lines.append("\n--- End Character Information ---")
    context_lines.append(f"\nUser's Question: {user_question}")
    context_lines.append("\nYour Answer (based on the character sheet and Pathfinder 2e rules):")
    
    full_prompt = "\n".join(context_lines)
    if 'st' in globals() and hasattr(st, 'session_state'): # Check if Streamlit context exists
        st.session_state.last_qa_prompt = full_prompt

    try:
        generation_config = genai.types.GenerationConfig(max_output_tokens=20000)
        response = model.generate_content(full_prompt, generation_config=generation_config)
        return response.text
    except Exception as e:
        print(f"Error answering question (Google Generative AI): {e}")
        # if 'response' in locals() and hasattr(response, 'prompt_feedback'):
        # print(f"Prompt Feedback: {response.prompt_feedback}")
        return f"Error answering question: {e}"
    

# --- Main Application Logic (analyze_character_sheet) ---
def analyze_character_sheet(char_file_bytes: bytes, char_data_dict: dict, google_api_key: str, llm_model_name: str) -> Dict[str, Any]:
    # char_file_bytes is the raw bytes of the uploaded file for hashing
    # char_data_dict is the json.load() output
    
    file_hash = hashlib.md5(char_file_bytes).hexdigest() # Generate hash from file bytes

    try:
        sheet = CharacterSheet(**char_data_dict)
    except Exception as e:
        return {"error": f"Failed to parse character sheet: {e}", "suggestions": [], "combat_ideas": []}
    
    all_suggestions = [] # ... (your audit checks) ...
    all_suggestions.extend(check_unspent_gold(sheet))
    all_suggestions.extend(check_equipment_runes(sheet))
    all_suggestions.extend(check_missing_feat_slots(sheet))
        all_suggestions.extend(check_constitution_score(sheet))
      all_suggestions.extend(check_basic_consumables(sheet))

    combat_ideas = []
    if google_api_key: 
        # Pass the hash and the dict to the cached function
        combat_ideas = get_llm_combat_suggestions_cached(file_hash, char_data_dict, google_api_key, llm_model_name)
    else:
        combat_ideas = ["Google AI Studio API key not provided..."]
    
    return {
        "character_name": sheet.build.name,
        "character_level": sheet.build.level,
        "character_class": sheet.build.class_name,
        "audit_suggestions": all_suggestions,
        "combat_ideas": combat_ideas,
        "parsed_sheet_object_dict": char_data_dict, 
        "parsed_sheet_object_direct": sheet,
        "file_content_hash": file_hash # Store hash for Q&A if needed
    }

# --- Streamlit UI Code ---

st.set_page_config(page_title="Pathfinder 2e Character Auditor", layout="wide")

# ... (st.image, st.title, st.caption, sidebar config as before) ...
st.image("https://cdn.paizo.com/image/product/catalog/PZO2101_180.jpeg", width=100) 
st.title("Pathfinder 2e Character Auditor & Advisor")
st.caption("Upload your Pathbuilder JSON export. Powered by Google Gemini.")

st.sidebar.header("Configuration")
google_api_key_input = st.sidebar.text_input(
    "Google AI Studio API Key", type="password", 
    help="Get your key from Google AI Studio. Your key is not stored by this app."
)
# LLM Model Selection
llm_model_select = st.sidebar.selectbox(
    "Select Gemini Model",
    ("gemini-2.5-flash-preview-05-20", "gemini-2.5-pro-preview-05-06", "gemini-2.0-flash”, “gemini-2.0-flash-lite"), # Add more models if you wish
    index=0, 
    help="Ensure the selected model is compatible with your API key access."
)

# --- End Sidebar Config ---

# Initialize session state variables (ensure all are present)
if 'analysis_done' not in st.session_state: st.session_state.analysis_done = False
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None
if 'last_llm_prompt' not in st.session_state: st.session_state.last_llm_prompt = ""
if 'last_qa_prompt' not in st.session_state: st.session_state.last_qa_prompt = ""
if 'qa_answer' not in st.session_state: st.session_state.qa_answer = ""
if 'user_question' not in st.session_state: st.session_state.user_question = ""

uploaded_file = st.file_uploader("Upload Pathbuilder JSON Export", type=["json"], key="char_json_upload")

if uploaded_file is not None:
    if st.button("Analyze Character Sheet", key="analyze_button"):
        st.session_state.qa_answer = ""
        st.session_state.user_question = ""
        st.session_state.last_qa_prompt = ""
        if not google_api_key_input:
            st.warning("Please enter your Google AI Studio API Key for LLM-powered features.")
        try:
            uploaded_file.seek(0)
            char_file_bytes_content = uploaded_file.read() # Read as bytes for hashing
            uploaded_file.seek(0) # Reset pointer again for json.load
            char_data_as_dict = json.load(uploaded_file) # Load into dict
            with st.spinner("Analyzing character... (LLM features may take a moment)"):
                # Pass the dict to analyze_character_sheet
                st.session_state.analysis_results = analyze_character_sheet(
                    char_file_bytes_content, # Pass bytes for hashing
                    char_data_as_dict,      # Pass dict for Pydantic & caching
                    google_api_key_input, 
                    llm_model_select
                )  
            st.session_state.analysis_done = True
            if "error" in st.session_state.analysis_results:
                st.error(st.session_state.analysis_results["error"])
                st.session_state.analysis_done = False
            else:
                st.success("Analysis Complete! View results in the tabs below.")
        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please upload a valid Pathbuilder JSON export.")
            st.session_state.analysis_done = False
        except Exception as e:
            st.error(f"An unexpected error occurred during analysis: {e}")
            st.session_state.analysis_done = False

if st.session_state.analysis_done and st.session_state.analysis_results and "error" not in st.session_state.analysis_results:
    results = st.session_state.analysis_results
    
    st.header(f"Results for: {results.get('character_name', 'N/A')}")
    st.caption(f"Level {results.get('character_level', 'N/A')} {results.get('character_class', 'N/A')}")

    # Use the direct object for simple UI flags if available, or re-parse for safety
    parsed_sheet_direct = results.get("parsed_sheet_object_direct")
    if parsed_sheet_direct:
        if parsed_sheet_direct.build.free_archetype_active:
            st.success("✅ Free Archetype variant rule detected as active.")
        else:
            st.info("ℹ️ Free Archetype variant rule does not appear to be active.")

    tab_audit, tab_combat_ideas, tab_qa, tab_prompts, tab_raw_data = st.tabs([
        "🔍 Character Audit", "💡 Combat Ideas (Gemini)", "❓ Ask a Question", 
        "📝 LLM Prompts", "📄 Raw Data"
    ])

    with tab_audit:
        st.subheader("Character Audit Suggestions")
        if results["audit_suggestions"]:
            for suggestion in results["audit_suggestions"]:
                # --- VISUAL POLISH FOR AUDIT SUGGESTIONS ---
                icon = "ℹ️" # Default info
                if any(keyword in suggestion.lower() for keyword in ["missing", "unselected", "lower than recommended"]):
                    icon = "⚠️" # Warning
                if "low gold" in suggestion.lower():
                    icon = "🪙" # Gold specific
                
                # Use st.expander for potentially long suggestions or just format directly
                # For now, simple icon + markdown
                st.markdown(f"{icon} {suggestion}")
                # Example with expander (if suggestions get very long):
                # with st.expander(f"{icon} {suggestion.split('.')[0]}"): # Show first sentence as title
                #    st.markdown(suggestion)
            
            # Add AoN links for feats as an example
            if parsed_sheet_direct and parsed_sheet_direct.build.processed_feats:
                st.markdown("---")
                st.markdown("**Quick Feat Links (Archives of Nethys):**")
                for feat in parsed_sheet_direct.build.processed_feats:
                    if feat.name and "unselected" not in feat.name.lower():
                        st.markdown(f"- {feat.name}: [Search AoN]({get_aon_link(feat.name)})")

        else: 
            st.success("✅ No major audit suggestions found!")
    
    with tab_combat_ideas:
        # ... (Combat ideas display as before, formatting was already addressed) ...
        st.subheader("Combat Turn Ideas (Powered by Gemini)")
        if results["combat_ideas"]:
            for idea_block in results["combat_ideas"]:
                lines = idea_block.strip().split('\n')
                if lines:
                    first_line = lines[0].strip()
                    if len(first_line) < 80 and not (first_line.startswith(("* ","- ","1.","2.","3.","4.","5."))):
                        st.markdown(f"**{first_line}**")
                        remaining_text = "\n".join(lines[1:]).strip()
                        if remaining_text: st.markdown(remaining_text)
                    else: st.markdown(idea_block) 
                    st.markdown("---")
        else: st.markdown("No combat ideas generated or an error occurred.")

    with tab_qa:
        st.subheader("Ask a Question About This Character")
        # Get the dict AND the hash for the cached Q&A function
        character_data_dict_for_qa = results.get("parsed_sheet_object_dict") 
        file_hash_for_qa = results.get("file_content_hash") # <--- ADD THIS LINE

        if not character_data_dict_for_qa:
            st.warning("Character data not available for Q&A. Please analyze a sheet first.")
        elif not file_hash_for_qa: # <--- ADD THIS CHECK (good practice)
            st.warning("File hash not available for Q&A. Please re-analyze the sheet.")
        elif not google_api_key_input:
            st.warning("Please enter your Google AI Studio API Key in the sidebar to use this feature.")
        else:
            st.session_state.user_question = st.text_area(
                "Your question about the character:", 
                value=st.session_state.user_question, height=100, key="user_character_question"
            )
            if st.button("Get AI Answer", key="ask_qa_button"):
                if st.session_state.user_question:
                    with st.spinner("Asking Gemini..."):
                        st.session_state.qa_answer = get_llm_character_qa_answer_cached(
                            file_hash_for_qa,             # Pass the hash first
                            character_data_dict_for_qa,   # Pass the dict second
                            st.session_state.user_question, 
                            google_api_key_input, 
                            llm_model_select
                        )
                else:
                    st.info("Please type a question.")
            
            if st.session_state.qa_answer:
                st.markdown("#### AI's Answer:")
                st.markdown(st.session_state.qa_answer)

    with tab_prompts: 
        # ... (LLM Prompts display as before) ...
        st.subheader("LLM Prompts Sent")
        if st.session_state.last_llm_prompt:
            with st.expander("Combat Suggestions Prompt"):
                st.text_area("Prompt:", value=st.session_state.last_llm_prompt, height=300, disabled=True, key="combat_prompt_display")
        else: st.info("No combat suggestion prompt generated.")
        if st.session_state.last_qa_prompt:
            with st.expander("Character Q&A Prompt"):
                st.text_area("Prompt:", value=st.session_state.last_qa_prompt, height=300, disabled=True, key="qa_prompt_display")
        else: st.info("No Q&A prompt generated.")

    with tab_raw_data: 
        # ... (Raw data display as before) ...
        st.subheader("Parsed Character Data (JSON)")
        try:
            if uploaded_file: # Ensure file is still "active"
                 uploaded_file.seek(0) 
                 display_data = json.load(uploaded_file)
                 st.json(display_data, expanded=False)
            else:
                st.info("No file currently uploaded for raw display.")
        except Exception as e: st.error(f"Could not display raw JSON: {e}")
# ... (Rest of the UI logic, error handling, and footer as before) ...
else:
    if st.session_state.analysis_done and st.session_state.analysis_results and "error" in st.session_state.analysis_results:
         st.error(f"Could not display full results due to an analysis error: {st.session_state.analysis_results.get('error')}")
    elif not uploaded_file:
        st.info("Awaiting JSON file upload to begin analysis.")

st.markdown("---")
st.markdown("Pathfinder 2e Character Auditor | Version 0.7 (Basic Consumables Check) | LLM features are experimental.")

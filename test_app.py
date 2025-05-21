import unittest
from app import CharacterSheet, Build, Abilities, check_key_ability_score

# Helper function to create CharacterSheet objects for testing
def create_test_char(key_ability_str: str, str_score: int, dex_score: int, con_score: int, int_score: int, wis_score: int, cha_score: int) -> CharacterSheet:
    """
    Creates a minimal CharacterSheet object for testing the check_key_ability_score function.
    """
    return CharacterSheet(
        success=True,
        build=Build(
            name="Test Character",
            class_name="Test Class", # Alias for class
            level=1,
            ancestry="Test Ancestry",
            heritage="Test Heritage",
            background="Test Background",
            keyability=key_ability_str,
            abilities=Abilities(
                str=str_score, # Using Pydantic alias 'str'
                dex=dex_score, # Using Pydantic alias 'dex'
                con=con_score, # Using Pydantic alias 'con'
                int=int_score, # Using Pydantic alias 'int'
                wis=wis_score, # Using Pydantic alias 'wis'
                cha=cha_score  # Using Pydantic alias 'cha'
            ),
            proficiencies={}, 
            feats_raw=[],     
            specials=[],      
            equipment=[],     
            money={"cp":0,"sp":0,"gp":0,"pp":0}, 
            armor=[],         
            spellCasters=[]   
        )
    )

class TestKeyAbilityScore(unittest.TestCase):
    """
    Test suite for the check_key_ability_score function.
    """

    def test_key_ability_highest(self):
        """Test when the key ability score is the highest."""
        character = create_test_char("str", 18, 16, 14, 12, 10, 8)
        suggestions = check_key_ability_score(character)
        self.assertEqual(suggestions, [], "Should be no suggestions when key ability is highest.")

    def test_key_ability_second_highest(self):
        """Test when the key ability score is the second highest."""
        character = create_test_char("dex", 18, 16, 14, 12, 10, 8)
        suggestions = check_key_ability_score(character)
        self.assertEqual(suggestions, [], "Should be no suggestions when key ability is second highest.")

    def test_key_ability_third_highest(self):
        """Test when the key ability score is the third highest."""
        character = create_test_char("con", 18, 16, 14, 12, 10, 8)
        suggestions = check_key_ability_score(character)
        self.assertEqual(len(suggestions), 1, "Should be one suggestion when key ability is third highest.")
        self.assertIn("not among the top two", suggestions[0])

    def test_key_ability_tied_for_highest(self):
        """Test when the key ability score is tied for highest."""
        character = create_test_char("str", 18, 18, 14, 12, 10, 8)
        suggestions = check_key_ability_score(character)
        self.assertEqual(suggestions, [], "Should be no suggestions when key ability is tied for highest.")
        
        character_dex = create_test_char("dex", 18, 18, 14, 12, 10, 8)
        suggestions_dex = check_key_ability_score(character_dex)
        self.assertEqual(suggestions_dex, [], "Should be no suggestions when key ability (dex) is tied for highest.")


    def test_key_ability_tied_for_second_highest(self):
        """Test when key ability is tied for second highest (and distinct from absolute highest)."""
        character = create_test_char("dex", 20, 18, 18, 12, 10, 8) # STR 20, DEX 18, CON 18
        suggestions = check_key_ability_score(character)
        self.assertEqual(suggestions, [], "Should be no suggestions when key ability (dex) is tied for second highest.")

        character_con = create_test_char("con", 20, 18, 18, 12, 10, 8) # STR 20, DEX 18, CON 18
        suggestions_con = check_key_ability_score(character_con)
        self.assertEqual(suggestions_con, [], "Should be no suggestions when key ability (con) is tied for second highest.")


    def test_key_ability_tied_for_third_highest(self):
        """Test when key ability is tied for third highest (and distinct from top two groups)."""
        # STR 20, DEX 18, CON 16, INT 16. Key: CON
        character = create_test_char("con", 20, 18, 16, 16, 10, 8)
        suggestions = check_key_ability_score(character)
        self.assertEqual(len(suggestions), 1, "Should be one suggestion when key ability is tied for third highest.")
        self.assertIn("not among the top two", suggestions[0])
        self.assertIn("CON (score 16)", suggestions[0])
        self.assertIn("top two highest ability scores (20, 18)", suggestions[0])

        # STR 20, DEX 18, CON 16, INT 16. Key: INT
        character_int = create_test_char("int", 20, 18, 16, 16, 10, 8)
        suggestions_int = check_key_ability_score(character_int)
        self.assertEqual(len(suggestions_int), 1, "Should be one suggestion when key ability (INT) is tied for third highest.")
        self.assertIn("INT (score 16)", suggestions_int[0])
        self.assertIn("top two highest ability scores (20, 18)", suggestions_int[0])

    def test_all_scores_same(self):
        """Test when all ability scores are the same."""
        character = create_test_char("int", 14, 14, 14, 14, 14, 14)
        suggestions = check_key_ability_score(character)
        self.assertEqual(suggestions, [], "Should be no suggestions when all scores are the same.")
        
        character_str = create_test_char("str", 14, 14, 14, 14, 14, 14)
        suggestions_str = check_key_ability_score(character_str)
        self.assertEqual(suggestions_str, [], "Should be no suggestions when all scores are the same (key str).")

if __name__ == '__main__':
    unittest.main()

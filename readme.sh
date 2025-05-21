# Pathfinder 2e Character Auditor & Advisor

A Streamlit web application designed to help Pathfinder 2nd Edition (PF2e) players and Game Masters audit character sheets exported from Pathbuilder. It identifies common character-building mistakes, offers suggestions for improvement, and leverages Google's Gemini Large Language Models (LLMs) for dynamic combat advice and character-specific Q&A.

## 🚀 Features

*   **Pathbuilder JSON Upload:** Easily upload your character's JSON export file from Pathbuilder.
*   **Automated Character Audits:**
    *   **💰 Unspent Gold:** Checks for excessively high or unusually low amounts of unspent gold relative to character level.
    *   **⚔️ Equipment Runes:** Verifies weapon and armor (potency, striking/resiliency) fundamental runes against level-based recommendations and checks for unfilled property rune slots.
    *   **🎓 Missing Feat Slots:** Detects unselected feats or potential discrepancies in expected vs. actual feat counts for Ancestry, Skill, General, Class, and Free Archetype feats.
    *   **📜 Free Archetype Detection:** Automatically identifies if the Free Archetype variant rule is likely in use based on feat selection.
*   **💡 LLM-Powered Combat Suggestions (via Google Gemini):**
    *   Provides 3-5 actionable combat turn ideas tailored to the character's class, feats, spells, and equipment.
    *   Utilizes a dynamically generated prompt based on the character sheet.
    *   Requires a Google AI Studio API Key.
*   **❓ LLM-Powered Character Q&A (via Google Gemini):**
    *   Allows users to ask specific questions about their character (e.g., "How does my Power Attack feat work?", "What are my strongest offensive spells?").
    *   The LLM answers based on the provided character sheet data and general PF2e knowledge.
    *   Requires a Google AI Studio API Key.
*   **🔗 Archives of Nethys Links:** Generates quick search links to Archives of Nethys for feats listed on the character sheet.
*   **📊 User-Friendly Interface:**
    *   Clear, tabbed layout for Audit Suggestions, Combat Ideas, Q&A, LLM Prompts, and Raw Data.
    *   Visual cues for audit suggestions (e.g., icons).
    *   Spinners for loading states during LLM calls.
*   **📄 Data Handling & Caching:**
    *   Uses Pydantic for robust parsing and validation of the Pathbuilder JSON structure.
    *   Caches LLM responses using `st.cache_data` to speed up repeated requests for the same character/query and reduce API calls.
    *   File content hashing ensures cache invalidation when the character sheet changes.

## ✨ How It Works

1.  **Upload:** The user uploads their Pathbuilder JSON character export.
2.  **Parse & Validate:** The application parses the JSON file into Pydantic models, validating the structure.
3.  **Audit:** A series of predefined checks are run against the character data to find common issues (gold, runes, feats).
4.  **LLM Interaction (Optional):**
    *   If a Google AI Studio API key is provided, a detailed prompt summarizing the character's abilities is constructed.
    *   This prompt is sent to the selected Google Gemini model to generate combat suggestions.
    *   For the Q&A feature, the character summary and user's question are sent to the LLM.
5.  **Display:** Results, suggestions, and LLM responses are presented to the user in an organized, tabbed interface.

## 🛠️ Technology Stack

*   **Python 3.x**
*   **Streamlit:** For the web application framework and UI.
*   **Pydantic:** For data validation and settings management (parsing the character JSON).
*   **Google Generative AI SDK (`google-generativeai`):** For interacting with Google Gemini LLMs.

## ⚙️ Setup and Usage

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-name>
    ```
2.  **Install dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
    *(You'll need to create a `requirements.txt` file. Based on your code, it should include at least: `streamlit`, `pydantic`, `google-generativeai`)*

3.  **Get a Google AI Studio API Key:**
    *   Visit [Google AI Studio](https://aistudio.google.com/) and obtain an API key.
4.  **Run the Streamlit app:**
    ```bash
    streamlit run pf2e_auditor_app.py
    ```
5.  **Use the App:**
    *   Open the provided local URL in your browser.
    *   Enter your Google AI Studio API Key in the sidebar (required for LLM features).
    *   Select your preferred Gemini model.
    *   Upload your Pathbuilder JSON file.
    *   Click "Analyze Character Sheet".
    *   Explore the results in the different tabs.

## 📝 LLM Prompts

The application dynamically generates prompts for the LLM based on the character's details. Examples of these prompts can be viewed in the "LLM Prompts" tab after an analysis is run, which can be helpful for understanding the AI's context or for debugging.

## 🔮 Future Enhancements (Ideas)

*   Deeper audits (e.g., skill proficiency progression, ability score allocation, consumable checks).
*   Contextual combat scenarios for LLM suggestions.
*   "Explain This" feature for audit points, linking to rules.
*   More sophisticated AoN integration (e.g., fetching descriptions).
*   (See project issues or contribute your own ideas!)

## 📄 Disclaimer

*   This is a fan-made tool intended for personal use and is not affiliated with Paizo Inc. or Pathbuilder.
*   Pathfinder is a registered trademark of Paizo Inc.
*   Always double-check character building decisions with official Paizo rulebooks and resources like Archives of Nethys.
*   LLM-generated content is for inspiration and should be critically evaluated for accuracy and applicability to your game.

import os
from pathlib import Path
import yaml
from click.testing import CliRunner

from ormd_cli.main import cli # Assuming your main CLI group is named 'cli'

def test_create_ormd_file():
    runner = CliRunner()
    test_filename = "test-created-doc.ormd"
    test_filepath = Path(test_filename)

    try:
        # Invoke the create command
        result = runner.invoke(cli, ['create', test_filename])

        assert result.exit_code == 0, f"CLI Error: {result.output}"
        assert test_filepath.exists(), "File was not created"

        # Read the content of the created file
        content = test_filepath.read_text(encoding='utf-8')

        # 1. Check for ORMD version comment
        assert content.startswith("<!-- ormd:0.1 -->\n"), "Missing or incorrect ORMD version comment"

        # 2. Extract and check front-matter
        parts = content.split("---\n")
        assert len(parts) >= 3, "Front-matter delimiters not found or incorrect structure"

        front_matter_str = parts[1]
        front_matter = yaml.safe_load(front_matter_str)

        assert front_matter is not None, "Front-matter is not valid YAML"

        # 3. Check title (derived from filename)
        expected_title = "Test Created Doc" # from "test-created-doc.ormd"
        assert front_matter.get("title") == expected_title, f"Incorrect title: expected '{expected_title}', got '{front_matter.get('title')}'"

        # 4. Check authors (empty list)
        assert front_matter.get("authors") == [], "Authors list is not empty"

        # 5. Check dates structure and presence
        assert "dates" in front_matter, "Dates field missing from front-matter"
        dates_data = front_matter.get("dates")
        assert isinstance(dates_data, dict), "Dates field is not a dictionary"
        assert "created" in dates_data, "created date missing"
        assert "modified" in dates_data, "modified date missing"

        # Check if dates are ISO format (simple check for string type and basic structure)
        # A more robust check might involve parsing with datetime.fromisoformat
        assert isinstance(dates_data["created"], str), "Created date is not a string"
        assert isinstance(dates_data["modified"], str), "Modified date is not a string"
        assert dates_data["created"].endswith("+00:00") or dates_data["created"].endswith("Z"), "Created date not in UTC ISO format"


        # 6. Check for an empty line after front-matter (body part)
        # The content should be "<!-- ormd:0.1 -->\n---\n...front_matter...\n---\n\n"
        # parts[2] should be the rest of the document after the second '---'
        # For a newly created file, this should be just a newline.
        assert parts[2] == "\n", f"Expected a single newline after front-matter, got: {repr(parts[2])}"

    finally:
        # Clean up the created file
        if test_filepath.exists():
            test_filepath.unlink()

if __name__ == "__main__":
    # This allows running the test directly for debugging, e.g., python -m pytest test_create_command.py
    # Or for simple execution: python ormd_cli/tests/test_create_command.py
    test_create_ormd_file()
    print("Test completed.")

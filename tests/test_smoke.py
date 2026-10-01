"""Basic import/configuration smoke tests. Run: python -m unittest discover -s tests"""
import unittest

class ProjectStructureTests(unittest.TestCase):
    def test_required_files_exist(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        for rel in ["app/main.py", "app/routes.py", "app/ai_service.py", "app/database.py",
                    "app/models.py", "app/templates/index.html", "app/templates/result.html",
                    "app/templates/all_users.html", "app/static/style.css", "requirements.txt"]:
            self.assertTrue((root / rel).is_file(), rel)

    def test_goal_fallback(self):
        from app.ai_service import demo_workout
        plan = demo_workout("general_wellness", "low")
        self.assertIn("DAY 1", plan)
        self.assertIn("DAY 7", plan)

if __name__ == "__main__":
    unittest.main()

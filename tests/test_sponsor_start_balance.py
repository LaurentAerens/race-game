import unittest
import os
import tempfile
import gc
import shutil
from src.database.career_db import CareerDatabase
from src.management.sponsor_manager import SponsorManager


class TestSponsorStartBalance(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.db_path = os.path.join(self.td, "test_sponsor_balance.db")
        self.db = CareerDatabase(self.db_path)
        self.sm = SponsorManager(self.db)

    def tearDown(self):
        if hasattr(self, "db"):
            del self.db
        gc.collect()
        if hasattr(self, "td") and os.path.exists(self.td):
            shutil.rmtree(self.td, ignore_errors=True)

    def test_starting_appeal_rating_is_at_most_10(self):
        """A brand new starter team in Tier 3 should start with an appeal rating <= 10/100."""
        p = self.db.get_player_team()
        appeal_data = self.sm.calculate_sponsor_appeal(p["id"])
        total_appeal = appeal_data["total_appeal"]

        self.assertLessEqual(total_appeal, 10, f"Starting appeal too high: {total_appeal}")
        self.assertGreaterEqual(total_appeal, 5, f"Starting appeal too low: {total_appeal}")
        self.assertEqual(appeal_data["form_pts"], 0.0, "Unproven team should have 0 form points")
        self.assertEqual(appeal_data["history_pts"], 0.0, "Unproven team should have 0 season history points")

    def test_normal_difficulty_starting_offers(self):
        """On NORMAL difficulty, starting offers should be 1 secondary and 2 minors (0 title)."""
        self.db.create_new_career("Test Racing Normal", "#ff4400", difficulty="NORMAL")
        p = self.db.get_player_team()
        offers = self.sm.get_sponsor_offers(p["id"])

        mid_offers = [o for o in offers if o["slot_tier"] == "MIDDLE"]
        min_offers = [o for o in offers if o["slot_tier"] == "MINOR"]
        title_offers = [o for o in offers if o["slot_tier"] == "TITLE"]

        self.assertEqual(len(mid_offers), 1, f"Expected 1 secondary offer, got {len(mid_offers)}")
        self.assertEqual(len(min_offers), 2, f"Expected 2 minor offers, got {len(min_offers)}")
        self.assertEqual(len(title_offers), 0, f"Expected 0 title offers, got {len(title_offers)}")
        self.assertEqual(len(offers), 3, f"Expected 3 total offers, got {len(offers)}")

    def test_very_easy_difficulty_starting_offers(self):
        """On VERY_EASY difficulty, starting offers should have a single minor more: 1 secondary and 3 minors."""
        self.db.create_new_career("Test Racing Very Easy", "#00dd88", difficulty="VERY_EASY")
        p = self.db.get_player_team()
        offers = self.sm.get_sponsor_offers(p["id"])

        mid_offers = [o for o in offers if o["slot_tier"] == "MIDDLE"]
        min_offers = [o for o in offers if o["slot_tier"] == "MINOR"]
        title_offers = [o for o in offers if o["slot_tier"] == "TITLE"]

        self.assertEqual(len(mid_offers), 1, f"Expected 1 secondary offer, got {len(mid_offers)}")
        self.assertEqual(len(min_offers), 3, f"Expected 3 minor offers on VERY_EASY, got {len(min_offers)}")
        self.assertEqual(len(title_offers), 0, f"Expected 0 title offers, got {len(title_offers)}")
        self.assertEqual(len(offers), 4, f"Expected 4 total offers on VERY_EASY, got {len(offers)}")

    def test_no_duplicate_brands_in_initial_offers(self):
        """Sponsor offers must not contain duplicate brands."""
        self.db.create_new_career("Test Racing Unique", "#0088ff", difficulty="VERY_EASY")
        p = self.db.get_player_team()
        offers = self.sm.get_sponsor_offers(p["id"])
        brand_names = [o["brand_name"] for o in offers]

        self.assertEqual(len(brand_names), len(set(brand_names)), f"Found duplicate brands: {brand_names}")

    def test_render_does_not_instantly_replenish_offers(self):
        """Calling check_and_generate_offers(is_progression=False) must not refill signed slots."""
        self.db.create_new_career("Test Racing Gating", "#ffaa00", difficulty="NORMAL")
        p = self.db.get_player_team()
        offers = self.sm.get_sponsor_offers(p["id"])
        self.assertEqual(len(offers), 3)

        # Sign one minor offer
        minor_to_sign = [o for o in offers if o["slot_tier"] == "MINOR"][0]
        success, _ = self.sm.sign_sponsor_offer(p["id"], minor_to_sign["id"])
        self.assertTrue(success)

        # Simulate 120 frames of UI rendering
        for _ in range(120):
            self.sm.check_and_generate_offers(p["id"], is_progression=False)

        offers_after_render = self.sm.get_sponsor_offers(p["id"])
        self.assertEqual(len(offers_after_render), 2, "Render loop should not immediately replace signed offer")

        # Now simulate progression (weekly/post-race)
        self.sm.check_and_generate_offers(p["id"], is_progression=True)
        offers_after_prog = self.sm.get_sponsor_offers(p["id"])
        self.assertEqual(len(offers_after_prog), 3, "Progression should bring in a replacement offer")


if __name__ == "__main__":
    unittest.main()

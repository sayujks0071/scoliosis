import os
import unittest

from scripts.generate_spine_daily_update import generate_report, parse_roadmap

# Create a temporary roadmap file for testing
TEMP_ROADMAP = "tests/temp_roadmap.md"
ROADMAP_CONTENT = """# Spine Submission Roadmap

**Target:** *Spine* (IF: 3.30, Q1, H-index: 300)
**Strategy:** "A computational framework predicting adolescent scoliosis onset" with clinical validation against published cohort data.
**Start Date:** 2026-02-23
**Target Submission Date:** 2026-04-06 (6 Weeks)

## Phase 1: Computational Framework (Weeks 1-2)

- [x] **Core Model:** Establish "Energy Deficit" model (`experiment_energy_deficit_window.py`).
- [x] **Rescue Cliff:** Validate "Rescue Cliff" at Anisotropy ~2.4 (Simulated in `outputs/sim/2026-02-22/`).
- [ ] **Spinal Jetlag:** Run "Spinal Jetlag" simulation to demonstrate circadian modulation of curvature.
- [ ] **Robustness:** Ensure model stability across parameter sweeps (Sensitivity Analysis).

## Phase 2: Clinical Validation (Weeks 3-4)

- [ ] **Cohort Data Extraction:** Extract clinical cohort data (Cobb angle distributions, progression rates) from published literature.
"""

class TestSpineUpdateScript(unittest.TestCase):

    def setUp(self):
        with open(TEMP_ROADMAP, "w") as f:
            f.write(ROADMAP_CONTENT)

    def tearDown(self):
        if os.path.exists(TEMP_ROADMAP):
            os.remove(TEMP_ROADMAP)

    def test_parse_roadmap(self):
        data, error = parse_roadmap(TEMP_ROADMAP)
        self.assertIsNone(error)
        self.assertEqual(data['total_tasks'], 5)
        self.assertEqual(data['completed_tasks'], 2)
        self.assertAlmostEqual(data['percent_complete'], 40.0)
        self.assertEqual(data['phases']['Phase 1: Computational Framework (Weeks 1-2)']['total'], 4)
        self.assertEqual(data['phases']['Phase 1: Computational Framework (Weeks 1-2)']['completed'], 2)

    def test_generate_report(self):
        data, error = parse_roadmap(TEMP_ROADMAP)
        report = generate_report(data)
        self.assertIn("**Target Journal:** Spine", report)
        self.assertIn("**Percent Complete:** 40.0%", report)
        self.assertIn("Phase 1: Computational Framework (Weeks 1-2)", report)

if __name__ == '__main__':
    unittest.main()

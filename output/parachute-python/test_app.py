import math
import unittest
from app import calculate, build_page


class ParachuteTests(unittest.TestCase):
    def setUp(self):
        self.p = dict(mass=19.471, diameter=math.sqrt(4*6.05/math.pi), cd=.8,
                      rho_open=1.173, rho_land=1.225, speed=14.32, height=450, target=8)

    def test_main(self):
        r = calculate(self.p)
        self.assertAlmostEqual(r['terminal_mps'], 8.03, places=2)
        self.assertAlmostEqual(r['drag_n'], 582.1, delta=2)
        self.assertGreater(r['ideal_landing_mps'], 8)
        self.assertFalse(r['meets_target_estimate'])

    def test_impact_at_zero_height_is_initial_speed(self):
        self.p['height'] = 0
        self.assertAlmostEqual(calculate(self.p)['ideal_landing_mps'], 14.32)

    def test_drag_scales_with_velocity_squared(self):
        a = calculate(self.p)['drag_n']
        self.p['speed'] *= 2
        self.assertAlmostEqual(calculate(self.p)['drag_n'], 4*a)

    def test_invalid_inputs(self):
        for bad in [0, -1, float('nan'), float('inf')]:
            self.p['cd'] = bad
            with self.assertRaises(ValueError):
                calculate(self.p)

    def test_page_has_all_components(self):
        page = build_page()
        for item in ['parachute-workshop', 'parachute-three', 'pw-physics', 'window.updateParachute3D']:
            self.assertIn(item, page)


if __name__ == '__main__':
    unittest.main()

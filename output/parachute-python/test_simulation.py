import io
import json
import math
import unittest
import zipfile
from simulation import G, run, fractions, config, convergence, compare_csv, mesh_study
from project_pack import bundle


class DynamicsTests(unittest.TestCase):
    def test_freefall_before_deployment(self):
        r=run({'height':100,'main_height':0,'drogue_delay':5,'max_time':10})
        for row in r['rows']:
            if row['time_s']<1:
                t=row['time_s']
                self.assertAlmostEqual(row['speed_mps'],G*t,places=8)
                self.assertAlmostEqual(row['height_m'],100-.5*G*t*t,places=8)
        self.assertAlmostEqual(r['summary']['duration_s'],math.sqrt(200/G),places=7)

    def test_event_and_ground(self):
        r=run({});s=r['summary']
        self.assertTrue(s['landed'])
        event=[row for row in r['rows'] if abs(row['time_s']-s['main_trigger_s'])<1e-8]
        self.assertTrue(event)
        self.assertAlmostEqual(event[0]['height_m'],450,places=6)
        self.assertAlmostEqual(s['landing_speed_mps'],math.sqrt(2*19.471*G/(1.225*.8*6.05)),delta=.003)
        self.assertIsNone(r['snatch_force_n'])

    def test_reefing_stages(self):
        p=config({'reef_ratio':.4,'main_fill':1,'reef_hold':2,'release_fill':1})
        self.assertEqual(fractions(10,p,10)[1],0)
        self.assertAlmostEqual(fractions(12,p,10)[1],.4)
        self.assertAlmostEqual(fractions(14,p,10)[1],1)
        self.assertEqual(fractions(12,p,10)[0],0)

    def test_6dof_reduces_to_vertical_when_symmetric(self):
        cfg={'height':60,'main_height':30,'lever':0,'tilt_deg':0}
        a=run(cfg);b=run({**cfg,'mode':'6dof'})
        self.assertAlmostEqual(a['summary']['landing_speed_mps'],b['summary']['landing_speed_mps'],places=9)
        self.assertEqual(b['summary']['max_tilt_deg'],0)
        self.assertEqual(b['summary']['drift_m'],0)

    def test_wind_symmetry(self):
        cfg={'mode':'6dof','height':80,'main_height':30,'tilt_deg':0,'lever':0}
        a=run({**cfg,'wind_x':5});b=run({**cfg,'wind_x':-5})
        self.assertGreater(a['rows'][-1]['x_m'],0)
        self.assertAlmostEqual(a['rows'][-1]['x_m'],-b['rows'][-1]['x_m'],places=8)
        self.assertAlmostEqual(a['summary']['landing_speed_mps'],b['summary']['landing_speed_mps'],places=8)

    def test_convergence_and_truncation(self):
        r=convergence({'height':80,'main_height':30})
        self.assertLess(r['fine_relative_change_percent']['landing_speed_mps'],.1)
        r=run({'max_time':10})
        self.assertFalse(r['summary']['landed'])
        self.assertIsNone(r['summary']['landing_speed_mps'])

    def test_rejects_bad_values(self):
        for bad in ({'mass':float('nan')},{'mode':'fake_fsi'},{'dt':0},{'height':50,'main_height':100},{'retain_drogue':'false'}):
            with self.assertRaises(ValueError):run(bad)


class VerificationTests(unittest.TestCase):
    def test_synthetic_interpolation_only_not_real_validation(self):
        p={'height':30,'main_height':10};r=run(p)
        unique={x['time_s']:x for x in r['rows']}
        rows=list(unique.values())[2:8]
        csv='time_s,force_n\n'+'\n'.join(f"{x['time_s']},{x['force_n']}" for x in rows)
        compared=compare_csv({'config':p,'csv':csv})
        self.assertLess(compared['metrics']['force_n']['rmse'],1e-8)
        self.assertEqual(compared['matched_count'],len(rows))

    def test_no_extrapolation(self):
        with self.assertRaises(ValueError):compare_csv({'csv':'time_s,force_n\n1001,1\n1002,2\n1003,3'})

    def test_mesh_sort_and_duplicates(self):
        r=mesh_study('h_m,cd\n0.02,0.8\n0.08,0.7\n0.04,0.78')
        self.assertEqual(r['levels'][0]['h_m'],.08)
        self.assertAlmostEqual(r['levels'][-1]['relative_change_percent'],2.5)
        with self.assertRaises(ValueError):mesh_study('h_m,cd\n0.1,0.7\n0.1,0.8\n0.01,0.8')

    def test_bundle_has_no_fabricated_solver_results(self):
        data=bundle({'config':{}})
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            manifest=json.loads(z.read('manifest.json'))
            self.assertEqual(manifest['status'],'PREPARATION_ONLY_NOT_SOLVED')
            self.assertIn('templates/permeability.csv',z.namelist())
            self.assertIn(b'facet normal',z.read('geometry/main_illustrative_surface.stl'))
            self.assertEqual(z.read('templates/drop_test.csv').decode().count('\n'),1)


if __name__=='__main__':unittest.main()

"""Functional source checks for the photo-guided 26 October additions."""
from unittest import TestCase

from tools.build_povo_campus import build_geometry, collision_boxes, is_breakable_glass
from tools.audit_povo_interior import audit_level


class Povo2AdditionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,levels,_=build_geometry()
        cls.spec=next(l['connection']['povo2'] for l in levels if l.get('connection'))
        cls.physics=collision_boxes(cls.boxes)

    def test_computer_room_has_monitors_and_classrooms_have_raked_seats(self):
        ground=next(l for l in self.spec['levels'] if l['floor']==0)
        rooms={r['id']:r for r in ground['rooms']}
        self.assertTrue(any(n.startswith('p2_ground_b106_monitor_') for n,_,_,_ in self.boxes))
        for name in ('b108','b109'):
            room=rooms[name]
            self.assertGreater(room['fitout']['seats'],0)
            self.assertEqual(room['fitout']['riser_metres'],.12)
            self.assertTrue(any(n.startswith('p2_ground_'+name+'_tier_') and hi[2]>lo[2]
                                for n,lo,hi,_ in self.boxes))
            self.assertTrue(any(n=='p2_ground_'+name+'_window_glass' and is_breakable_glass(box)
                                for box in self.boxes for n,_,_,_ in [box]))

    def test_both_cibio_offices_are_reachable_and_decorative_doors_stay_sealed(self):
        basement=next(l for l in self.spec['levels'] if l['floor']==-1)
        report,_,_=audit_level(self.physics,dict(id=basement['id'],floor_elevation_local=basement['z']),
                              basement['audit_stations'],width=.82,height=1.85)
        self.assertEqual(report['status'],'passed',report)
        self.assertEqual(len(basement['rooms']),2)
        doors=[b for b in self.boxes if b[0].startswith('p2_basement_cibio_closed_office_')]
        self.assertEqual(len(doors),6)
        for _,lo,hi,_ in doors:
            x=hi[0]+.05;y=(lo[1]+hi[1])/2
            self.assertTrue(any(m=='wall' and a[0]<x<b[0] and a[1]<y<b[1]
                                and a[2]<1.5<b[2] for _,a,b,m in self.physics))

    def test_temporary_aula_has_a_continuous_supported_centre_aisle(self):
        self.assertTrue(self.spec['additions']['temporary_aula'])
        for x,y,z in self.spec['additions']['aula_path']:
            self.assertTrue(any(m.startswith('floor_') and lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1]
                                and abs(hi[2]-z)<.02 for _,lo,hi,m in self.physics))
            blockers=[n for n,lo,hi,m in self.physics if lo[0]<x+.41 and hi[0]>x-.41
                      and lo[1]<y+.41 and hi[1]>y-.41 and lo[2]<z+1.85 and hi[2]>z+.37]
            self.assertFalse(blockers,blockers)

    def test_all_new_boxes_have_positive_volume_and_known_materials(self):
        from tools.build_povo_campus import COLORS
        names=[n for n,_,_,_ in self.boxes]
        self.assertEqual(len(names),len(set(names)))
        for name,lo,hi,material in self.boxes:
            self.assertTrue(all(a<b for a,b in zip(lo,hi)),name)
            self.assertIn(material,COLORS,name)

    def test_basement_exit_reaches_the_yard_and_existing_street(self):
        from tools.audit_povo_yard import audit
        result=audit()
        self.assertEqual(result['status'],'passed',result)
        self.assertEqual(result['stair_and_landing_samples'],22)
        self.assertFalse(result['failures'])

    def test_existing_bridge_and_povo2_floor_elevations_are_preserved(self):
        self.assertEqual([l['z'] for l in self.spec['levels']],[-3.2,.4,4])
        self.assertEqual(self.spec['stairs']['portals'][0]['centre'][2],4)
        _,_,_,levels,_=build_geometry()
        self.assertEqual(next(l['connection'] for l in levels if l.get('connection'))['floor_local_metres'],11.2)

    def test_corrected_reception_corridor_and_right_turns(self):
        cfg=self.spec['additions']['config'];corridor=cfg['ground_corridor']
        pc=cfg['ground_rooms'][0]
        self.assertEqual(pc['kind'],'computer')
        self.assertTrue(all(r['bounds'][3]==corridor[1] for r in cfg['ground_rooms']))
        self.assertGreater(corridor[2]-corridor[0],corridor[3]-corridor[1])
        self.assertLessEqual(corridor[3],self.spec['stairs']['bounds'][1])
        pc,b108,b109=cfg['ground_rooms']
        self.assertEqual(pc['bounds'][0],b108['bounds'][2])
        self.assertEqual(b108['bounds'][0],b109['bounds'][2])
        self.assertEqual(cfg['stair_entry']['door'],[20.5,22])
        self.assertFalse(any(n.startswith(('p2_ground_reception_stair_door_',
                                          'p2_ground_stair_vestibule')) for n,_,_,_ in self.boxes))
        # Exit the existing stair eastward: south then west is right/right.
        self.assertLess(cfg['cibio_corridor'][1],22)
        self.assertLess(cfg['cibio_corridor'][0],16.5)
        self.assertTrue(all(r[3]<=cfg['cibio_corridor'][1] for r in cfg['cibio_offices']))
        # Left/north, then right/east is the independent exit branch.
        self.assertGreater(cfg['basement_exit']['return_corridor'][1],22)
        self.assertGreater(cfg['basement_exit']['return_corridor'][2],20)

    def test_aula_is_on_the_lobby_opposite_short_edge_and_faces_entry(self):
        cfg=self.spec['additions']['config'];lobby=cfg['aula_lobby'];aula=cfg['aula_magna']
        self.assertEqual(aula[0],lobby[2])
        self.assertLess(lobby[3]-lobby[1],lobby[2]-lobby[0])
        self.assertLess(max(lobby[1],aula[1]),min(lobby[3],aula[3]))
        chairs={n:(lo,hi) for n,lo,hi,_ in self.boxes if n.startswith('p2_ground_aula_chair_')}
        for name,(lo,hi) in chairs.items():
            back=next(b for b in self.boxes if b[0]==name.replace('_chair_','_back_'))
            self.assertGreater(back[2][0],hi[0])
        self.assertFalse(any(n.startswith('exterior_povo2_terrace_guard_') for n,_,_,_ in self.boxes))
        stairs=cfg['basement_exit']['steel_stair'];door=cfg['basement_exit']['inside_stair']
        self.assertEqual(stairs[0],door[2])
        self.assertLess(stairs[1],27.5)
        self.assertGreater(stairs[3],27.5)

    def test_sloped_road_bounds_do_not_false_positive_but_real_intersections_do(self):
        from tools.povo2_interiors import mesh_intersects_box
        mesh=dict(vertices=[(0,0,1),(10,0,11),(10,1,11),(0,1,1),
                            (0,0,1.2),(10,0,11.2),(10,1,11.2),(0,1,1.2)],
                  faces=[(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
        self.assertFalse(mesh_intersects_box(mesh,((8,.2,2),(9,.8,3))))
        self.assertTrue(mesh_intersects_box(mesh,((8,.2,9.1),(9,.8,9.3))))
        self.assertTrue(mesh_intersects_box(mesh,((8.5,.3,9.55),(8.51,.4,9.56))))

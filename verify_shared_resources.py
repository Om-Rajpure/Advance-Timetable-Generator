

import unittest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath('backend'))

from engine.scheduler import TimetableScheduler

class TestSharedResources(unittest.TestCase):
    def test_shared_room_assignment(self):
        """
        Verify that 2 divisions share the SAME room pool.
        """
        # 1. Setup Data with SMALL room pool (1 room) and 2 Classes
        context = {
            "branchData": {
                "academicYears": ["SE", "TE"],
                "divisions": {"SE": ["A"], "TE": ["A"]},
                "classrooms": ["Shared-Room-1"], # Only 1 room!
                "labs": [],
                "workingDays": ["Mon", "Tue"],
                "slotsPerDay": 4
            },
            "smartInputData": {
                "teachers": [{"name": "T1", "subjects": ["Math"]}, {"name": "T2", "subjects": ["Physics"]}],
                "subjects": [
                    {"name": "Math", "year": "SE", "weeklyLectures": 2, "type": "Theory"},
                    {"name": "Physics", "year": "TE", "weeklyLectures": 2, "type": "Theory"}
                ],
                "teacherSubjectMap": [
                     {"subjectName": "Math", "teacherName": "T1"},
                     {"subjectName": "Physics", "teacherName": "T2"}
                ]
            }
        }
        
        scheduler = TimetableScheduler(context)
        result = scheduler.generate()
        
        self.assertTrue(result['success'])
        
        # Verify assignments
        timetable = result['timetables']
        se_timetable = timetable['SE']['A']['timetable']
        te_timetable = timetable['TE']['A']['timetable']
        
        # Flatten
        all_slots = []
        for day, slots in se_timetable.items():
            all_slots.extend(slots)
        for day, slots in te_timetable.items():
            all_slots.extend(slots)
            
        print(f"\nGenerated {len(all_slots)} slots.")
        
        # Check Rooms
        used_rooms = set(s['room'] for s in all_slots)
        print(f"Used Rooms: {used_rooms}")
        
        self.assertIn("Shared-Room-1", used_rooms)
        # Should NOT contain legacy defaults like 'Classroom-SE-A'
        self.assertFalse(any("Classroom-" in r for r in used_rooms))
        
        # Check for Collisions (Two classes in same room at same time)
        occupancy = {}
        for s in all_slots:
            key = (s['day'], s['slot'], s['room'])
            if key in occupancy:
                print(f"COLLISION: {key} used by {occupancy[key]} AND {s['year']}")
            occupancy[key] = s['year']
            
        print("Verification Complete: Shared Room Used correctly.")

if __name__ == "__main__":
    unittest.main()

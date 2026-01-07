
import unittest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath('backend'))

from engine.scheduler import TimetableScheduler

class TestCompaction(unittest.TestCase):
    def test_daily_compaction(self):
        """
        Verify that schedules are compacted (no gaps).
        """
        # 1. Setup Context
        context = {
            "branchData": {
                "academicYears": ["SE"],
                "divisions": {"SE": ["A"]},
                "classrooms": ["Room-1", "Room-2"],
                "labs": [],
                "workingDays": ["Mon"],
                "slotsPerDay": 8,
            },
            "smartInputData": {
                # Create a scenario where gaps MIGHT occur naturally
                # e.g., huge load, scarce rooms? 
                # Or just check standard gen is compact.
                "teachers": [{"name": "T1", "subjects": ["Math"]}, {"name": "T2", "subjects": ["Physics"]}],
                "subjects": [
                    {"name": "Math", "year": "SE", "weeklyLectures": 2, "type": "Theory"},
                    {"name": "Physics", "year": "SE", "weeklyLectures": 2, "type": "Theory"}
                ],
                "teacherSubjectMap": [
                     {"subjectName": "Math", "teacherName": "T1"},
                     {"subjectName": "Physics", "teacherName": "T2"}
                ]
            }
        }
        
        # Inject Recess for realism (Slot 4, index 3? Or Slot 4 index 3)
        # Recess usually handled by config.
        # Let's trust Scheduler defaults (no recess config passed -> standard logic).
        
        scheduler = TimetableScheduler(context)
        result = scheduler.generate()
        self.assertTrue(result['success'])
        
        timetable = result['timetables']['SE']['A']['timetable']
        monday_slots = timetable.get('Mon', [])
        
        print("\nGenerated Slots for Monday:")
        for s in monday_slots:
            print(f"Slot {s['slot']}: {s['subject']} ({s.get('room','?')})")
            
        # Verify Contiguity
        sorted_slots = sorted([s['slot'] for s in monday_slots])
        
        if sorted_slots:
            min_s = min(sorted_slots)
            max_s = max(sorted_slots)
            count = len(sorted_slots)
            
            # If compact, max - min + 1 == count
            # (assuming unique slots)
            
            # Check for recess?
            # If recess is at index 3, and we span across it, we might have a gap in INDICES but not logic.
            # But here we simply check if we find any unexpected gaps.
            
            # Simple check: Are they 0, 1, 2, 3?
            expected = list(range(min_s, min_s + count))
            self.assertEqual(sorted_slots, expected, f"Slots are not compact! Got {sorted_slots}")
            
        print("Compaction Verified: Slots are contiguous.")

if __name__ == "__main__":
    unittest.main()

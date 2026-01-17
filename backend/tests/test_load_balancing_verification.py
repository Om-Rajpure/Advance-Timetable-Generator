
import sys
import os
import unittest
from unittest.mock import MagicMock

# Adjust path to find backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from engine.load_manager import TeacherLoadManager
from engine.state_manager import TimetableState

class TestTeacherLoadManager(unittest.TestCase):
    def setUp(self):
        self.mock_context = {
            'smartInputData': {
                'teachers': [
                    {'name': 'T1', 'subjects': ['Math'], 'workingHours': 8},
                    {'name': 'T2', 'subjects': ['Math'], 'workingHours': 8},
                    {'name': 'T3', 'subjects': ['Physics'], 'workingHours': 8}
                ],
                'teacherSubjectMap': [
                    {'teacherName': 'T3', 'subjectName': 'Physics, Chemistry'} # Comma separated test
                ],
                'subjects': []
            },
            'branchData': {
                'slotsPerDay': 8
            }
        }
        self.manager = TeacherLoadManager(self.mock_context)
        self.state = MagicMock()
        # Mock availability to always be True initially
        self.state.is_teacher_available.return_value = True

    def test_theory_continuity(self):
        print("\nTesting Theory Continuity...")
        # First assignment
        t1 = self.manager.get_or_select_theory_teacher('Math', 'SE', 'A')
        print(f"Assigned {t1} to Math SE-A")
        
        # Second assignment (Same class) - MUST be same teacher
        t2 = self.manager.get_or_select_theory_teacher('Math', 'SE', 'A')
        self.assertEqual(t1, t2, "Theory teacher should be locked for Subject+Year+Div")
        
        # Different division - Logic creates new assignment (could be same or different based on load)
        # Since T1 has load now (if we commit), T2 might be picked.
        # But wait, get_or_select doesn't commit load. Commit happens on assignment.
        # Let's manually commit load for T1
        self.manager.commit_load(t1, 'Monday', 1)
        self.manager.commit_load(t1, 'Tuesday', 1)
        
        t3 = self.manager.get_or_select_theory_teacher('Math', 'SE', 'B')
        print(f"Assigned {t3} to Math SE-B (after T1 has load)")
        
        # If T1 has load, T2 (load 0) should be picked for balance
        if t1 == 'T1':
            self.assertEqual(t3, 'T2', "Should pick T2 for balance")

    def test_lab_continuity(self):
        print("\nTesting Lab Continuity...")
        # Assign Lab to Batch A
        t_lab_a = self.manager.get_best_teacher_for_lab('Math', 'SE', 'A', 'B1', 'Monday', 0, 2, self.state)
        self.assertIsNotNone(t_lab_a)
        
        # Lock check
        t_lab_a_retry = self.manager.get_best_teacher_for_lab('Math', 'SE', 'A', 'B1', 'Tuesday', 0, 2, self.state)
        self.assertEqual(t_lab_a, t_lab_a_retry, "Lab teacher should be locked per batch")
        
        # Batch B - can be different
        # Let's increase load for t_lab_a
        self.manager.commit_load(t_lab_a, 'Monday', 2)
        
        t_lab_b = self.manager.get_best_teacher_for_lab('Math', 'SE', 'A', 'B2', 'Monday', 0, 2, self.state)
        print(f"Batch B1: {t_lab_a}, Batch B2: {t_lab_b}")
        
    def test_theory_lab_preference(self):
        print("\nTesting Theory -> Lab Preference...")
        # Assign Theory Teacher
        theory_t = self.manager.get_or_select_theory_teacher('Physics', 'TE', 'A')
        
        # Try to assign Lab for SAME subject
        # Ensure theory teacher is available
        lab_t = self.manager.get_best_teacher_for_lab('Physics', 'TE', 'A', 'B1', 'Monday', 0, 2, self.state)
        
        self.assertEqual(theory_t, lab_t, "Should prefer Theory teacher for Lab if available")

if __name__ == '__main__':
    unittest.main()


import sys
import os
import unittest
import copy

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from engine.data_normalizer import DataNormalizer, NormalizationError

class TestDataNormalizer(unittest.TestCase):
    
    def setUp(self):
        self.base_context = {
            "branchData": {
                "academicYears": ["SE"],
                "workingDays": ["Mon", "Tue"],
                "divisions": {"SE": ["A", "B"]},
                "labs": [{"name": "L1", "capacity": 20}],
                "labBatchesPerYear": {"SE": 3}
            },
            "smartInputData": {
                "subjects": [],
                "teachers": [{"name": "T1", "subjects": ["Sub1"]}]
            }
        }

    def test_missing_data_failure(self):
        """Test failure on missing context data"""
        with self.assertRaises(NormalizationError):
            DataNormalizer({}).normalize()

    def test_subject_cleanup(self):
        """Test trimming and casing of subjects"""
        ctx = copy.deepcopy(self.base_context)
        # Reduce divisions to just A for this test to avoid completeness error for B
        ctx['branchData']['divisions']['SE'] = ["A"]
        
        ctx['smartInputData']['subjects'] = [
            {"name": "  Dirty Name  ", "year": "SE", "division": "A", "type": "lecture"}
        ]
        
        norm = DataNormalizer(ctx)
        result = norm.normalize()
        s = result['smartInputData']['subjects'][0]
        
        self.assertEqual(s['name'], "Dirty Name")
        self.assertEqual(s['type'], "Lecture")

    def test_division_expansion(self):
        """Test expanding generic SE subject to SE-A and SE-B"""
        ctx = copy.deepcopy(self.base_context)
        ctx['smartInputData']['subjects'] = [
            # Generic SE subject (no division)
            {"name": "Generic Sub", "year": "SE", "division": "", "type": "Lecture", "lecturesPerWeek": 3}
        ]
        
        norm = DataNormalizer(ctx)
        result = norm.normalize()
        subjects = result['smartInputData']['subjects']
        
        # Should now have 2 subjects: SE-A and SE-B
        # And since we expanded, completeness check should pass for A and B!
        self.assertEqual(len(subjects), 2)
        divisions = sorted([s['division'] for s in subjects])
        self.assertEqual(divisions, ["A", "B"])

    def test_completeness_failure(self):
        """Test failure if a division has no theory subjects"""
        ctx = copy.deepcopy(self.base_context)
        # SE-A has subject, SE-B has NONE
        ctx['smartInputData']['subjects'] = [
            {"name": "Sub1", "year": "SE", "division": "A", "type": "Lecture"}
        ]
        
        norm = DataNormalizer(ctx)
        with self.assertRaises(NormalizationError) as cm:
            norm.normalize()
        
        print(f"\nCaught Expected Error: {cm.exception}")
        # Case insensitive match
        self.assertIn("class se-b has no theory subjects", str(cm.exception).lower())

    def test_batch_validation_success(self):
        """Test successful batch validation"""
        ctx = copy.deepcopy(self.base_context)
        ctx['smartInputData']['subjects'] = [
            {"name": "Theory", "year": "SE", "division": "A", "type": "Lecture"},
            {"name": "Theory", "year": "SE", "division": "B", "type": "Lecture"},
            {"name": "Lab", "year": "SE", "division": "A", "type": "Practical"},
            {"name": "Lab", "year": "SE", "division": "B", "type": "Practical"}
        ]
        
        norm = DataNormalizer(ctx)
        result = norm.normalize()
        self.assertTrue(result)
        # Verify batch config was enforced/checked
        self.assertEqual(result['branchData']['labBatchesPerYear']['SE'], 3)


if __name__ == '__main__':
    unittest.main()

"""
Simple Direct Test of Generation Engine

Tests the core components step by step.
"""

import sys
import os

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.')
sys.path.insert(0, backend_dir)

from engine.state_manager import TimetableState
from engine.candidate_generator import CandidateGenerator
from engine.heuristics import SlotHeuristics

# Minimal test data
context = {
    "branchData": {
        "academicYears": ["SE"],
        "divisions": {"SE": ["A"]},
        "slotsPerDay": 6,
        "rooms": ["Room-1", "Room-2"],
        "labs": []
    },
    "smartInputData": {
        "subjects": [
            {"name": "ML", "year": "SE", "division": "A", "lecturesPerWeek": 2}
        ],
        "teachers": [
            {"name": "Neha", "subjects": ["ML"]},
            {"name": "John", "subjects": []}  # Can teach anything
        ]
    }
}

print("=" * 60)
print("Direct Component Test")
print("=" * 60)

# Test 1: State Manager
print("\n[TEST 1] State Manager")
print("-" * 60)
state = TimetableState(context)
slots = state.generate_slot_grid()
print(f"✅ Generated {len(slots)} total slots")
print(f"Sample: {slots[0]}")

# Test 2: Candidate Generator
print("\n[TEST 2] Candidate Generator")
print("-" * 60)
candidate_gen = CandidateGenerator(state, context)
test_slot = slots[0]
candidates = candidate_gen.generate_candidates(test_slot)
print(f"✅ Generated {len(candidates)} candidates for first slot")
if candidates:
    print(f"Sample candidate: {candidates[0]}")
else:
    print("❌ NO CANDIDATES GENERATED - This is the problem!")

# Test 3: Heuristics
print("\n[TEST 3] Heuristics")
print("-" * 60)
heuristics = SlotHeuristics(state, context)
ordered = heuristics.order_slots(slots[:10])
print(f"✅ Ordered {len(ordered)} slots")
if ordered:
    print(f"First slot to fill: {ordered[0]}")

print("\n" + "=" * 60)
print("Component tests completed!")
print("=" * 60)

if not candidates:
    print("\n⚠️  ISSUE FOUND: No candidates generated")
    print("This means the algorithm can't find valid assignments")
    print("Likely cause: Subject matching logic in candidate_generator.py")

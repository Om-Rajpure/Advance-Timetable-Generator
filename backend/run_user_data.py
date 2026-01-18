
import json
import sys
import os
import random

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from engine.scheduler import TimetableScheduler

DATA_FILE = r'c:\Users\omraj\OneDrive\Desktop\Adv Timetable Gen\test_data\go_live_data.json'

def run_user_data_test():
    print(f"🚀 LOADING USER DATA FROM: {DATA_FILE}")
    
    if not os.path.exists(DATA_FILE):
        print(f"❌ File not found!")
        return
        
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            
        branch_data = data.get('branchData', {})
        smart_input = data.get('smartInputData', {})
        
        # VALIDATE DATA
        subjects = smart_input.get('subjects', [])
        teachers = smart_input.get('teachers', [])
        teacher_map = smart_input.get('teacherSubjectMap', [])
        
        print(f"📊 DATA STATS:")
        print(f"  - Subjects: {len(subjects)}")
        print(f"  - Teachers: {len(teachers)}")
        print(f"  - Mappings: {len(teacher_map)}")
        
        # AUTO-FIX: If no mappings, assign randomly
        if len(teacher_map) == 0:
            print("\n⚠️ WARNING: No Teacher-Subject mappings found!")
            print("🛠️ AUTO-FIX: Randomly assigning teachers to subjects for TESTING purposes...")
            
            # Create mapping
            new_map = []
            
            # Simple strategy: Round robin or Random
            # Ensure teachers have subjects list properly updated if needed (Engine uses map or expects subject in teacher list?)
            # The Scheduler uses `state.teacher_subject_map` derived from `teacherSubjectMap`.
            
            # We need to populate `teacherSubjectMap` in smart input
            # Format: { "teacherId": "t1", "subjectId": "s1" } (Based on common input format)
            # OR Check `constraints/base.py` or `state_manager.py` to see expected format.
            # Usually: `{"teacherName": ..., "subjectName": ...}` or IDs.
            # Let's check smart input keys from file: Teachers have "id", Subjects have "id".
            # The dummy data in `repro_full_dataset.py` used `teacherName` and `subjectName`.
            # Let's assume the engine handles ID mapping if IDs are provided.
            # BUT safely, we should map NAMES if possible, or check how `DataNormalizer` handles it.
            # DataNormalizer Expects `teacherSubjectMap` list of objects.
            
            t_ids = [t['id'] for t in teachers]
            
            for sub in subjects:
                # Assign 1 random teacher
                assigned_tid = random.choice(t_ids)
                new_map.append({
                    "teacherId": assigned_tid,
                    "subjectId": sub['id'],
                    # Optional names for debugging
                    "debug_sName": sub['name']
                })
            
            smart_input['teacherSubjectMap'] = new_map
            print(f"  -> Assigned {len(new_map)} mappings.")
            
        
        # PREPARE CONTEXT
        context = {
            "branchData": branch_data,
            "smartInputData": smart_input
        }
        
        # EXECUTE
        print("\n⚙️ STARTING SCHEDULER...")
        scheduler = TimetableScheduler(context, max_iterations=500) # Give it 500 iters
        result = scheduler.generate()
        
        # REPORT
        print("\n" + "="*40)
        print(f"RESULTS (Success: {result.get('success')})")
        print("="*40)
        
        if result.get('stage'):
            print(f"Stage: {result.get('stage')}")
            
        if result.get('success'):
            print("✅ Timetable Generated Successfully!")
            tt = result.get('timetables', {})
            total_slots = 0
            for yr, divs in tt.items():
                for div, d_data in divs.items():
                    s_count = 0
                    if isinstance(d_data.get('timetable'), dict):
                         s_count = sum(len(v) for v in d_data['timetable'].values())
                    print(f"  - {yr} {div}: {s_count} slots")
                    total_slots += s_count
            print(f"Total Slots: {total_slots}")
        else:
            print("❌ Generation Failed.")
            print(f"Message: {result.get('message')}")
            if result.get('blockers'):
                print("Blockers:")
                for b in result.get('blockers'):
                    print(f"  - {b.get('issue')}: {b.get('details')}")
                    
    except Exception as e:
        import traceback
        print(f"\n❌ CRASHED: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_user_data_test()

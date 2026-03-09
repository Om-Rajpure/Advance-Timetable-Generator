
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

print("PROBE START")

try:
    from utils.time_utils import calculate_time_slots
    print("Imported calculate_time_slots")
    res = calculate_time_slots({})
    print("calculate_time_slots({}) =", res)
except Exception:
    traceback.print_exc()

print("Initialising Scheduler...")
try:
    from engine.scheduler import TimetableScheduler
    context = {
        "branchData": {"academicYears": ["SE"], "divisions": {"SE": ["A"]}}, 
        "smartInputData": {"subjects": [], "teachers": []}
    }
    scheduler = TimetableScheduler(context)
    print("Scheduler Initialized.")
    
    print("Running _validate_inputs...")
    # Directly call internal validation
    try:
        scheduler._validate_inputs()
        print("_validate_inputs passed.")
    except:
        traceback.print_exc()

except Exception:
    traceback.print_exc()

print("PROBE END")

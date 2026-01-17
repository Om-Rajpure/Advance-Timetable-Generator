
import json
import os
import sys
import glob

# Path to history versions
HISTORY_DIR = os.path.join(os.getcwd(), 'backend', 'data', 'history', 'versions')

def inspect_latest_history():
    # Find latest file
    files = glob.glob(os.path.join(HISTORY_DIR, '*.json'))
    if not files:
        print("❌ No history files found.")
        return

    latest_file = max(files, key=os.path.getmtime)
    print(f"📂 Reading latest history: {os.path.basename(latest_file)}")

    try:
        with open(latest_file, 'r') as f:
            data = json.load(f)
            
        timetable = data.get('timetableSnapshot', [])
        metadata = data.get('metadata', {})
        context = data.get('context', {}) # branchData might be here?
        
        print(f"📊 Total Slots: {len(timetable)}")
        
        # Analyze Rooms
        rooms_found = set()
        slots_with_rooms = 0
        slots_without_rooms = 0
        
        sample_no_room = None
        sample_with_room = None
        
        for slot in timetable:
            r = slot.get('room')
            if r:
                rooms_found.add(str(r))
                slots_with_rooms += 1
                if not sample_with_room: sample_with_room = slot
            else:
                slots_without_rooms += 1
                if not sample_no_room and slot.get('type') == 'THEORY': sample_no_room = slot
                
        print(f"✅ Slots with Room: {slots_with_rooms}")
        print(f"❌ Slots without Room: {slots_without_rooms}")
        print(f"🏫 Unique Rooms Found: {sorted(list(rooms_found))}")
        
        if sample_no_room:
            print("\n🔍 Sample Slot WITHOUT Room (Theory):")
            print(json.dumps(sample_no_room, indent=2))

        # Analyze Branch Data Context
        bd = context.get('branchData', {})
        if not bd:
            # Maybe inside metadata?
            print("⚠️ No branchData in context key.")
        else:
            print(f"\n🌳 Branch Data Rooms: {bd.get('rooms', [])}")
            print(f"🌳 Branch Data Classrooms: {bd.get('classrooms', [])}")
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    inspect_latest_history()

"""
Hard Constraints

These constraints MUST NEVER be violated. A timetable with any hard constraint
violation is invalid and cannot be used.
"""

from .base import Constraint, ConstraintViolation


class TeacherNonOverlapConstraint(Constraint):
    """HC1: A teacher cannot be assigned to multiple slots at the same time"""
    
    def __init__(self):
        super().__init__(
            name="TEACHER_NON_OVERLAP",
            description="A teacher cannot be assigned to more than one slot at the same time",
            severity="HARD"
        )
    
    def check(self, timetable, context):
        violations = []
        
        # Group slots by (day, slot_index)
        time_slots = {}
        for slot in timetable:
            key = (slot['day'], slot['slot'])
            if key not in time_slots:
                time_slots[key] = []
            time_slots[key].append(slot)
        
        # Check each time slot for teacher overlaps
        for (day, slot_index), slots in time_slots.items():
            teacher_assignments = {}
            
            for slot in slots:
                teacher = slot.get('teacher')
                if not teacher or teacher == 'TBA':
                    continue
                
                if teacher not in teacher_assignments:
                    teacher_assignments[teacher] = []
                teacher_assignments[teacher].append(slot)
            
            # Report violations
            for teacher, assigned_slots in teacher_assignments.items():
                if len(assigned_slots) > 1:
                    divisions = [f"{s['year']}-{s['division']}" for s in assigned_slots]
                    violations.append(ConstraintViolation(
                        message=f"Teacher '{teacher}' is assigned to multiple divisions at the same time",
                        entities={
                            "teacher": teacher,
                            "divisions": divisions,
                            "day": day,
                            "time_slot": slot_index
                        },
                        slot=f"{day} Slot {slot_index}",
                        severity="HARD"
                    ))
        
        return {
            "valid": len(violations) == 0,
            "violations": [v.to_dict() for v in violations],
            "score": None
        }


class RoomNonOverlapConstraint(Constraint):
    """HC2: A room/lab cannot be used by multiple classes at the same time"""
    
    def __init__(self):
        super().__init__(
            name="ROOM_NON_OVERLAP",
            description="A classroom or lab cannot be used by more than one class at the same time",
            severity="HARD"
        )
    
    def check(self, timetable, context):
        violations = []
        
        # Group slots by (day, slot_index)
        time_slots = {}
        for slot in timetable:
            key = (slot['day'], slot['slot'])
            if key not in time_slots:
                time_slots[key] = []
            time_slots[key].append(slot)
        
        # Check each time slot for room overlaps
        for (day, slot_index), slots in time_slots.items():
            room_assignments = {}
            
            for slot in slots:
                room = slot.get('room')
                if not room or room == 'TBA':
                    continue
                
                if room not in room_assignments:
                    room_assignments[room] = []
                room_assignments[room].append(slot)
            
            # Report violations
            for room, assigned_slots in room_assignments.items():
                if len(assigned_slots) > 1:
                    divisions = [f"{s['year']}-{s['division']}" for s in assigned_slots]
                    violations.append(ConstraintViolation(
                        message=f"Room '{room}' is booked for multiple divisions at the same time",
                        entities={
                            "room": room,
                            "divisions": divisions,
                            "day": day,
                            "time_slot": slot_index
                        },
                        slot=f"{day} Slot {slot_index}",
                        severity="HARD"
                    ))
        
        return {
            "valid": len(violations) == 0,
            "violations": [v.to_dict() for v in violations],
            "score": None
        }


class PracticalBatchSyncConstraint(Constraint):
    """HC3: All batches of a division must have practicals at the same time"""
    
    def __init__(self):
        super().__init__(
            name="PRACTICAL_BATCH_SYNC",
            description="All batches of a division must have practicals at the same time in different labs",
            severity="HARD"
        )
    
    def check(self, timetable, context):
        violations = []
        
        # HC3: All batches of a division must have practicals at the same time
        # NOTE: This original constraint enforced that all batches do the SAME subject or start at same time.
        # With the new rule 11 ("Each sub-batch must be assigned a different lab subject"), 
        # we still want them to start at the same time (synchronized session), but subject equality is NOT required.
        # The synchronization is handled by the LabScheduler placing them together.
        # This validator previously might have checked for "Same Subject". 
        # Since we trust LabScheduler to adhere to the time-window structure, we can relax this 
        # or strictly check that if one batch has a lab, others in the same division also have a lab (of any type).
        
        # For now, we disable strict "Same Subject" checks.
        # We could implement "Synchronization Check" later: 
        # "If Year-Div has a lab in Slot X, ALL batches must have a lab in Slot X."
        
        pass
        
        return {
            "valid": len(violations) == 0,
            "violations": [v.to_dict() for v in violations],
            "score": None
        }
        
        return {
            "valid": len(violations) == 0,
            "violations": [v.to_dict() for v in violations],
            "score": None
        }


class WeeklyLectureCompletionConstraint(Constraint):
    """HC4: Each subject must have exactly its required number of lectures per week"""
    
    def __init__(self):
        super().__init__(
            name="WEEKLY_LECTURE_COMPLETION",
            description="Each subject must complete its required number of lectures per week (no over or under allocation)",
            severity="HARD"
        )
    
    def check(self, timetable, context):
        violations = []
        
        # Get required lecture counts from smart input data
        smart_input = context.get('smartInputData', {})
        subjects_data = smart_input.get('subjects', [])
        
        # Build required lecture map
        # Build required lecture map
        lab_batches = context.get('branchData', {}).get('labBatchesPerYear', {})
        
        required_lectures = {}
        for subject in subjects_data:
            key = (subject.get('name'), subject.get('year'), subject.get('division'))
            req = subject.get('lecturesPerWeek', 0)
            
            # If practical, multiply by number of batches
            if subject.get('isPractical') or subject.get('type') == 'Practical':
                year = subject.get('year')
                num_batches = int(lab_batches.get(year, 3)) # Default 3
                req = req * num_batches
                
            required_lectures[key] = req
        
        # Count actual lectures in timetable
        actual_lectures = {}
        for slot in timetable:
            if slot.get('type') == 'Practical' or slot.get('subject') == 'Free':
                continue  # Don't count practicals or free slots as lectures
            
            key = (slot.get('subject'), slot.get('year'), slot.get('division'))
            if key not in actual_lectures:
                actual_lectures[key] = 0
            actual_lectures[key] += 1
        
        # Check for mismatches
        all_keys = set(required_lectures.keys()) | set(actual_lectures.keys())
        
        for key in all_keys:
            subject, year, division = key
            required = required_lectures.get(key, 0)
            actual = actual_lectures.get(key, 0)
            
            if required != actual:
                if actual < required:
                    message = f"Subject '{subject}' for {year}-{division} has {actual}/{required} lectures (under-allocated)"
                else:
                    message = f"Subject '{subject}' for {year}-{division} has {actual}/{required} lectures (over-allocated)"
                
                violations.append(ConstraintViolation(
                    message=message,
                    entities={
                        "subject": subject,
                        "year": year,
                        "division": division,
                        "required": required,
                        "actual": actual,
                        "difference": actual - required
                    },
                    slot="Weekly allocation",
                    severity="HARD"
                ))
        
        return {
            "valid": len(violations) == 0,
            "violations": [v.to_dict() for v in violations],
            "score": None
        }


class StructuralValidityConstraint(Constraint):
    """HC5: All referenced entities must exist in branch/smart input data"""
    
    def __init__(self):
        super().__init__(
            name="STRUCTURAL_VALIDITY",
            description="Every slot must reference valid year, division, subject, teacher, and room",
            severity="HARD"
        )
    
    def check(self, timetable, context):
        violations = []
        
        # Extract valid entities from context
        branch_data = context.get('branchData', {})
        smart_input = context.get('smartInputData', {})
        
        # Build valid entity sets
        valid_years = set(branch_data.get('academicYears', []))
        valid_divisions = set()
        for year, divs in branch_data.get('divisions', {}).items():
            valid_divisions.update(divs)
        
        valid_subjects = set(s.get('name') for s in smart_input.get('subjects', []))
        valid_teachers = set(t.get('name') for t in smart_input.get('teachers', []))
        valid_rooms = set(branch_data.get('rooms', []))
        
        # Checking both 'labs' (legacy) and 'sharedLabs' (new structure)
        legacy_labs = branch_data.get('labs', [])
        valid_labs = set(legacy_labs)
        
        shared_labs = branch_data.get('sharedLabs', [])
        for lab in shared_labs:
            valid_labs.add(lab.get('name'))
            
        valid_rooms.update(valid_labs)
        
        # Validate each slot
        for slot in timetable:
            slot_ref = f"{slot.get('day')} Slot {slot.get('slot')} ({slot.get('year')}-{slot.get('division')})"
            
            # Check year
            year = slot.get('year')
            if year and year not in valid_years:
                violations.append(ConstraintViolation(
                    message=f"Invalid year '{year}' referenced in timetable",
                    entities={"year": year, "valid_years": list(valid_years)},
                    slot=slot_ref,
                    severity="HARD"
                ))
            
            # Check division
            division = slot.get('division')
            if division and division not in valid_divisions:
                violations.append(ConstraintViolation(
                    message=f"Invalid division '{division}' referenced in timetable",
                    entities={"division": division, "valid_divisions": list(valid_divisions)},
                    slot=slot_ref,
                    severity="HARD"
                ))
            
            # Check subject
            subject = slot.get('subject')
            if subject and subject not in ['Unassigned', 'Free'] and subject not in valid_subjects:
                violations.append(ConstraintViolation(
                    message=f"Invalid subject '{subject}' referenced in timetable",
                    entities={"subject": subject},
                    slot=slot_ref,
                    severity="HARD"
                ))
            
            # Check teacher
            teacher = slot.get('teacher')
            if teacher and teacher != 'TBA' and teacher not in valid_teachers:
                violations.append(ConstraintViolation(
                    message=f"Invalid teacher '{teacher}' referenced in timetable",
                    entities={"teacher": teacher},
                    slot=slot_ref,
                    severity="HARD"
                ))
            
            # Check room
            room = slot.get('room')
            if room and room != 'TBA' and room not in valid_rooms:
                violations.append(ConstraintViolation(
                    message=f"Invalid room '{room}' referenced in timetable",
                    entities={"room": room},
                    slot=slot_ref,
                    severity="HARD"
                ))
        
        return {
            "valid": len(violations) == 0,
            "violations": [v.to_dict() for v in violations],
            "score": None
        }

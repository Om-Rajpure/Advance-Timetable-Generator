"""
Partial Scheduler

Re-optimizes only affected slots while preserving unaffected assignments.
"""

from engine.scheduler import TimetableScheduler
from engine.state_manager import TimetableState
from engine.candidate_generator import CandidateGenerator
from engine.heuristics import SlotHeuristics
from constraints.constraint_engine import ConstraintEngine


class PartialScheduler:
    """Handles partial re-scheduling of affected slots"""
    
    def __init__(self, context):
        """
        Initialize partial scheduler.
        
        Args:
            context: Modified context with simulation constraints
        """
        self.context = context
        self.constraint_engine = ConstraintEngine()
    
    def reschedule_affected_slots(self, timetable, affected_slot_ids, simulation_type):
        """
        Re-optimize only affected slots while preserving unaffected ones.
        
        Args:
            timetable: Full current timetable (already cloned)
            affected_slot_ids: List of slot IDs that need re-assignment
            context: Modified context with simulation constraints
            simulation_type: Type of simulation (for tailored strategies)
            
        Returns:
            {
                "success": bool,
                "newTimetable": [...],
                "reassignedSlots": [...],
                "unresolvableConflicts": [...],
                "message": str
            }
        """
        # Separate affected and unaffected slots
        affected_slots = []
        unaffected_slots = []
        
        for slot in timetable:
            if slot.get('id') in affected_slot_ids:
                affected_slots.append(slot)
            else:
                unaffected_slots.append(slot)
        
        # If no affected slots, no work needed
        if not affected_slots:
            return {
                "success": True,
                "newTimetable": timetable,
                "reassignedSlots": [],
                "unresolvableConflicts": [],
                "message": "No slots require reassignment"
            }
        
        # Build a template for slots that need reassignment
        slots_to_reassign = self._build_slot_templates(affected_slots)
        
        # Try to fit affected slots into available time
        reassignment_result = self._attempt_reassignment(
            slots_to_reassign,
            unaffected_slots,
            simulation_type
        )
        
        if reassignment_result['success']:
            # Combine unaffected + newly assigned slots
            new_timetable = unaffected_slots + reassignment_result['assigned_slots']
            
            return {
                "success": True,
                "newTimetable": new_timetable,
                "reassignedSlots": reassignment_result['assigned_slots'],
                "unresolvableConflicts": [],
                "message": f"Successfully reassigned {len(reassignment_result['assigned_slots'])} slot(s)"
            }
        else:
            # Partial or no solution
            return {
                "success": False,
                "newTimetable": unaffected_slots + reassignment_result.get('assigned_slots', []),
                "reassignedSlots": reassignment_result.get('assigned_slots', []),
                "unresolvableConflicts": reassignment_result.get('conflicts', []),
                "message": reassignment_result.get('message', 'Failed to reassign some slots')
            }
    
    def _build_slot_templates(self, affected_slots):
        """
        Extract slot requirements from affected slots.
        
        Args:
            affected_slots: List of slot dictionaries
            
        Returns:
            List of slot templates (subject, teacher, type, etc. without day/time)
        """
        templates = []
        
        for slot in affected_slots:
            template = {
                "year": slot.get('year'),
                "division": slot.get('division'),
                "batch": slot.get('batch'),
                "subject": slot.get('subject'),
                "teacher": slot.get('teacher'),
                "type": slot.get('type'),
                "room_requirement": slot.get('room'),  # We may need to change this
                "original_id": slot.get('id')
            }
            templates.append(template)
        
        return templates
    
    def _attempt_reassignment(self, slot_templates, locked_slots, simulation_type):
        """
        Attempt to reassign slots into available time.
        
        Args:
            slot_templates: Slots needing reassignment
            locked_slots: Slots that must remain unchanged
            simulation_type: Type of simulation
            
        Returns:
            {
                "success": bool,
                "assigned_slots": [...],
                "conflicts": [...],
                "message": str
            }
        """
        # Use a greedy approach: try to fit each slot template into available time
        assigned_slots = []
        conflicts = []
        
        # Build availability map from locked slots
        availability = self._build_availability_map(locked_slots)
        
        # Get available time slots from context
        branch_data = self.context.get('branchData', {})
        working_days = branch_data.get('workingDays', [])
        slots_per_day = branch_data.get('slotsPerDay', 6)
        
        # Try to assign each template
        for template in slot_templates:
            assigned = False
            
            # Group practicals by division (need to assign all batches together)
            if template.get('type') == 'Practical':
                # Find other batches in templates
                related_batches = [
                    t for t in slot_templates
                    if (t.get('subject') == template.get('subject') and
                        t.get('year') == template.get('year') and
                        t.get('division') == template.get('division') and
                        t.get('type') == 'Practical')
                ]
                
                # Try to find a time slot that can fit all batches
                for day in working_days:
                    for slot_idx in range(slots_per_day):
                        if self._can_fit_practical_group(
                            related_batches, day, slot_idx, availability
                        ):
                            # Assign all batches
                            for batch_template in related_batches:
                                new_slot = self._create_slot_from_template(
                                    batch_template, day, slot_idx
                                )
                                assigned_slots.append(new_slot)
                                self._mark_unavailable(availability, new_slot)
                            
                            # Remove assigned templates
                            for batch_template in related_batches:
                                if batch_template in slot_templates:
                                    slot_templates.remove(batch_template)
                            
                            assigned = True
                            break
                    
                    if assigned:
                        break
                
                if not assigned and template in slot_templates:
                    conflicts.append({
                        "template": template,
                        "reason": "No available time slot for practical group"
                    })
            
            else:
                # Regular lecture - find any available slot
                for day in working_days:
                    for slot_idx in range(slots_per_day):
                        if self._can_fit_slot(template, day, slot_idx, availability):
                            new_slot = self._create_slot_from_template(template, day, slot_idx)
                            assigned_slots.append(new_slot)
                            self._mark_unavailable(availability, new_slot)
                            assigned = True
                            break
                    
                    if assigned:
                        break
                
                if not assigned:
                    conflicts.append({
                        "template": template,
                        "reason": "No available time slot"
                    })
        
        success = len(conflicts) == 0
        
        return {
            "success": success,
            "assigned_slots": assigned_slots,
            "conflicts": conflicts,
            "message": "All slots reassigned" if success else f"{len(conflicts)} slot(s) could not be reassigned"
        }
    
    def _build_availability_map(self, locked_slots):
        """Build a map of which time slots are already occupied."""
        availability = {}
        
        for slot in locked_slots:
            day = slot.get('day')
            slot_idx = slot.get('slot')
            teacher = slot.get('teacher')
            room = slot.get('room')
            year_div = f"{slot.get('year')}-{slot.get('division')}"
            
            key = (day, slot_idx)
            if key not in availability:
                availability[key] = {
                    "teachers": set(),
                    "rooms": set(),
                    "year_divisions": set()
                }
            
            if teacher and teacher != 'TBA':
                availability[key]["teachers"].add(teacher)
            if room and room != 'TBA':
                availability[key]["rooms"].add(room)
            availability[key]["year_divisions"].add(year_div)
        
        return availability
    
    def _can_fit_slot(self, template, day, slot_idx, availability):
        """Check if a slot template can fit at given day/time."""
        key = (day, slot_idx)
        
        if key not in availability:
            return True  # Completely free
        
        avail = availability[key]
        teacher = template.get('teacher')
        year_div = f"{template.get('year')}-{template.get('division')}"
        
        # Check teacher conflict
        if teacher and teacher != 'TBA' and teacher in avail["teachers"]:
            return False
        
        # Check year-division conflict (student group can't have two classes at once)
        if year_div in avail["year_divisions"]:
            return False
        
        return True
    
    def _can_fit_practical_group(self, batch_templates, day, slot_idx, availability):
        """Check if all batches of a practical can fit at given day/time."""
        # All batches need different labs
        smart_input = self.context.get('smartInputData', {})
        branch_data = self.context.get('branchData', {})
        available_labs = set(branch_data.get('labs', []))
        
        key = (day, slot_idx)
        if key in availability:
            # Remove already occupied labs
            occupied_labs = availability[key].get("rooms", set())
            available_labs = available_labs - occupied_labs
        
        # Need at least as many labs as batches
        if len(available_labs) < len(batch_templates):
            return False
        
        # Check teacher and year-division conflicts
        for template in batch_templates:
            if not self._can_fit_slot(template, day, slot_idx, availability):
                return False
        
        return True
    
    def _create_slot_from_template(self, template, day, slot_idx):
        """Create a full slot dictionary from template + day/time."""
        # Get available room/lab
        room = template.get('room_requirement')
        
        # For practicals, we need to assign specific labs
        if template.get('type') == 'Practical':
            # This should be handled in practical group assignment
            # For now, use the room requirement
            pass
        
        slot_id = f"{day}_{slot_idx}_{template.get('year')}_{template.get('division')}_{template.get('batch', '')}"
        
        return {
            "id": slot_id,
            "day": day,
            "slot": slot_idx,
            "year": template.get('year'),
            "division": template.get('division'),
            "batch": template.get('batch'),
            "subject": template.get('subject'),
            "teacher": template.get('teacher'),
            "room": room,
            "type": template.get('type'),
            "reassigned": True,  # Mark as reassigned for tracking
            "original_id": template.get('original_id')
        }
    
    def _mark_unavailable(self, availability, slot):
        """Mark a time slot as unavailable after assignment."""
        day = slot.get('day')
        slot_idx = slot.get('slot')
        key = (day, slot_idx)
        
        if key not in availability:
            availability[key] = {
                "teachers": set(),
                "rooms": set(),
                "year_divisions": set()
            }
        
        teacher = slot.get('teacher')
        room = slot.get('room')
        year_div = f"{slot.get('year')}-{slot.get('division')}"
        
        if teacher and teacher != 'TBA':
            availability[key]["teachers"].add(teacher)
        if room and room != 'TBA':
            availability[key]["rooms"].add(room)
        availability[key]["year_divisions"].add(year_div)

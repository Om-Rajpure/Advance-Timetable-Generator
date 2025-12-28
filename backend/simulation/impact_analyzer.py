"""
Impact Analyzer

Identifies which slots in the timetable are affected by a given simulation change.
"""


class ImpactAnalyzer:
    """Analyzes impact of simulation changes on timetable"""
    
    def __init__(self, timetable, context):
        """
        Initialize analyzer.
        
        Args:
            timetable: Current timetable (list of slots)
            context: Branch and smart input context
        """
        self.timetable = timetable
        self.context = context
    
    def analyze_teacher_impact(self, teacher_name, unavailable_spec):
        """
        Find slots affected by teacher unavailability.
        
        Args:
            teacher_name: Name of unavailable teacher
            unavailable_spec: {
                "days": ["Monday", "Wednesday"],  # Optional
                "slots": [0, 1, 2],  # Optional (slot indices)
                "fullWeek": bool  # If true, teacher is completely unavailable
            }
            
        Returns:
            {
                "affected_slot_ids": [...],
                "affected_slots": [slot objects],
                "impact_summary": "X slots need reassignment"
            }
        """
        affected_slots = []
        
        for slot in self.timetable:
            # Check if this slot uses the teacher
            if slot.get('teacher') != teacher_name:
                continue
            
            # Full week unavailability
            if unavailable_spec.get('fullWeek', False):
                affected_slots.append(slot)
                continue
            
            # Specific days unavailability
            unavailable_days = unavailable_spec.get('days', [])
            if unavailable_days and slot.get('day') in unavailable_days:
                affected_slots.append(slot)
                continue
            
            # Specific slot indices unavailability
            unavailable_slot_indices = unavailable_spec.get('slots', [])
            if unavailable_slot_indices and slot.get('slot') in unavailable_slot_indices:
                affected_slots.append(slot)
                continue
        
        affected_slot_ids = [slot.get('id') for slot in affected_slots]
        
        return {
            "affected_slot_ids": affected_slot_ids,
            "affected_slots": affected_slots,
            "impact_summary": f"{len(affected_slots)} slot(s) need reassignment for teacher '{teacher_name}'"
        }
    
    def analyze_lab_impact(self, lab_name):
        """
        Find slots affected by lab removal/unavailability.
        
        Args:
            lab_name: Name of unavailable lab
            
        Returns:
            {
                "affected_slot_ids": [...],
                "affected_slots": [slot objects],
                "impact_summary": "X practicals need reassignment"
            }
        """
        affected_slots = []
        
        for slot in self.timetable:
            # Check if this slot uses the lab
            if slot.get('room') == lab_name and slot.get('type') == 'Practical':
                affected_slots.append(slot)
        
        affected_slot_ids = [slot.get('id') for slot in affected_slots]
        
        return {
            "affected_slot_ids": affected_slot_ids,
            "affected_slots": affected_slots,
            "impact_summary": f"{len(affected_slots)} practical(s) need reassignment from lab '{lab_name}'"
        }
    
    def analyze_time_restriction_impact(self, removed_days=None, removed_slots=None):
        """
        Find slots affected by time restrictions (day/slot removal).
        
        Args:
            removed_days: List of days no longer available (e.g., ["Saturday"])
            removed_slots: List of slot indices no longer available
            
        Returns:
            {
                "affected_slot_ids": [...],
                "affected_slots": [slot objects],
                "impact_summary": "X slots need reassignment due to time restrictions"
            }
        """
        affected_slots = []
        removed_days = removed_days or []
        removed_slots = removed_slots or []
        
        for slot in self.timetable:
            # Check if slot is on a removed day
            if slot.get('day') in removed_days:
                affected_slots.append(slot)
                continue
            
            # Check if slot is at a removed time
            if slot.get('slot') in removed_slots:
                affected_slots.append(slot)
                continue
        
        affected_slot_ids = [slot.get('id') for slot in affected_slots]
        
        return {
            "affected_slot_ids": affected_slot_ids,
            "affected_slots": affected_slots,
            "impact_summary": f"{len(affected_slots)} slot(s) need reassignment due to time restrictions"
        }
    
    def get_dependent_slots(self, affected_slot_ids):
        """
        Expand affected slots to include dependent slots.
        
        For example:
        - If one batch of a practical is affected, all batches must be affected
          (due to batch synchronization constraint)
        - If a subject needs redistribution, we might need to consider
          weekly lecture completion
        
        Args:
            affected_slot_ids: Initial list of affected slot IDs
            
        Returns:
            {
                "expanded_slot_ids": [...],
                "expansion_reason": "Included dependent practical batch slots"
            }
        """
        expanded_ids = set(affected_slot_ids)
        expansion_reasons = []
        
        # Build mapping of affected slots
        affected_slot_map = {
            slot.get('id'): slot 
            for slot in self.timetable 
            if slot.get('id') in affected_slot_ids
        }
        
        # Check for practical batch dependencies
        for slot_id, slot in affected_slot_map.items():
            if slot.get('type') == 'Practical':
                # Find all batches of the same practical
                subject = slot.get('subject')
                year = slot.get('year')
                division = slot.get('division')
                day = slot.get('day')
                slot_index = slot.get('slot')
                
                # All batches at the same time for this practical
                for other_slot in self.timetable:
                    if (other_slot.get('type') == 'Practical' and
                        other_slot.get('subject') == subject and
                        other_slot.get('year') == year and
                        other_slot.get('division') == division and
                        other_slot.get('day') == day and
                        other_slot.get('slot') == slot_index and
                        other_slot.get('id') not in expanded_ids):
                        
                        expanded_ids.add(other_slot.get('id'))
                        expansion_reasons.append(
                            f"Included batch {other_slot.get('batch')} " +
                            f"for practical {subject} (batch sync requirement)"
                        )
        
        return {
            "expanded_slot_ids": list(expanded_ids),
            "expansion_reason": "; ".join(expansion_reasons) if expansion_reasons else "No expansion needed"
        }
    
    def get_resource_bottlenecks(self, impact_type, removed_resource=None):
        """
        Identify potential resource bottlenecks after simulation.
        
        Args:
            impact_type: 'teacher', 'lab', or 'time'
            removed_resource: Name of removed resource (if applicable)
            
        Returns:
            {
                "bottlenecks": [...],
                "warnings": [...]
            }
        """
        bottlenecks = []
        warnings = []
        
        if impact_type == 'lab' and removed_resource:
            # Check remaining lab capacity
            branch_data = self.context.get('branchData', {})
            all_labs = branch_data.get('labs', [])
            remaining_labs = [lab for lab in all_labs if lab != removed_resource]
            
            # Count practicals needing labs
            smart_input = self.context.get('smartInputData', {})
            practical_subjects = [
                s for s in smart_input.get('subjects', []) 
                if s.get('type') == 'Practical'
            ]
            
            # Max concurrent batches needed
            max_batches = max(
                (s.get('batches', 3) for s in practical_subjects),
                default=0
            )
            
            if max_batches > len(remaining_labs):
                bottlenecks.append({
                    "resource": "labs",
                    "required": max_batches,
                    "available": len(remaining_labs),
                    "severity": "high"
                })
                warnings.append(
                    f"Insufficient labs: need {max_batches} concurrent labs " +
                    f"but only {len(remaining_labs)} available after removing {removed_resource}"
                )
        
        return {
            "bottlenecks": bottlenecks,
            "warnings": warnings
        }

"""
Candidate Generator

Generates valid candidate assignments for each slot using smart filtering
and constraint-aware logic.
"""


class CandidateGenerator:
    """Generates candidate assignments for timetable slots"""
    
    def __init__(self, state, context):
        """
        Initialize candidate generator.
        
        Args:
            state: TimetableState instance
            context: Generation context with branch/smart input data
        """
        self.state = state
        self.context = context
        self.branch_data = context.get('branchData', {})
        self.smart_input = context.get('smartInputData', {})
    
    def generate_candidates(self, slot_info):
        """
        Generate all valid candidate assignments for a slot.
        
        Args:
            slot_info: Dictionary with day, slot, year, division
        
        Returns:
            List of candidate assignments with scores
        """
        day = slot_info['day']
        slot_index = slot_info['slot']
        year = slot_info['year']
        division = slot_info['division']
        
        # Determine if this should be a practical or lecture
        # Check if we need practicals for any subject
        practical_candidates = self._generate_practical_candidates(slot_info)
        lecture_candidates = self._generate_lecture_candidates(slot_info)
        
        # Combine and sort by score
        all_candidates = practical_candidates + lecture_candidates
        all_candidates.sort(key=lambda x: x.get('score', 0))
        
        # Always add a "Free" slot candidate as the last resort
        # This allows the scheduler to leave a slot empty if necessary
        free_candidate = {
            'day': day,
            'slot': slot_index,
            'year': year,
            'division': division,
            'subject': 'Free',
            'teacher': 'TBA',
            'room': 'TBA',
            'type': 'Free',
            'batch': None,
            'score': 1000  # High score so it's tried last
        }
        all_candidates.append(free_candidate)
        
        return all_candidates
    
    def _generate_lecture_candidates(self, slot_info):
        """Generate lecture candidates"""
        candidates = []
        day = slot_info['day']
        slot_index = slot_info['slot']
        year = slot_info['year']
        division = slot_info['division']
        
        # Get subjects for this year/division
        subjects = self.smart_input.get('subjects', [])
        
        # Get explicit teacher map
        teacher_subject_map = self.smart_input.get('teacherSubjectMap', [])
        # Map: subject -> [teacher_names]
        tm_map = {}
        for entry in teacher_subject_map:
            s_name = entry.get('subjectName')
            t_name = entry.get('teacherName')
            if s_name and t_name:
                if s_name not in tm_map: tm_map[s_name] = []
                tm_map[s_name].append(t_name)
        
        for subject_data in subjects:
            if (subject_data.get('year') != year or 
                subject_data.get('division') != division):
                continue
            
            # Skip if practical
            if subject_data.get('isPractical') or subject_data.get('type') == 'Practical':
                continue
                
            subject_name = subject_data.get('name')
            
            # Check if we need more lectures for this subject
            remaining = self.state.get_remaining_lectures(subject_name, year, division)
            if remaining <= 0:
                continue
            
            # Find available teachers for this subject
            teachers = self.smart_input.get('teachers', [])
            
            # Filter valid teachers for this subject
            valid_teacher_names = []
            
            # 1. Use explicit map if exists for this subject
            if subject_name in tm_map:
                valid_teacher_names = tm_map[subject_name]
            else:
                # 2. Use general competence list
                for t in teachers:
                    t_subs = t.get('subjects', [])
                    if subject_name in t_subs:
                        valid_teacher_names.append(t.get('name'))
            
            # If no teachers found for subject, we (strictly) cannot schedule. (Rule 5)
            if not valid_teacher_names:
                continue

            for teacher_name in valid_teacher_names:
                # Check if teacher is available
                if not self.state.is_teacher_available(teacher_name, day, slot_index):
                    continue
                
                # Find valid CLASSROOMS (Rule 22: Classrooms only for theory)
                # Ideally get from branch_data specific to year?
                # branch_data['classrooms'] might be a Dict { "SE": ["Room1"] } or List.
                # Let's handle both.
                classrooms_config = self.branch_data.get('classrooms', {})
                valid_rooms = []
                
                if isinstance(classrooms_config, dict):
                     valid_rooms = classrooms_config.get(year, [])
                     if not valid_rooms: 
                         # Fallback to all values if year specific not found?
                         # Or fallback to global 'rooms' list but exclude labs?
                         pass
                elif isinstance(classrooms_config, list):
                     valid_rooms = classrooms_config
                
                # If no specific classrooms found, try `rooms` but filter against `labs`
                if not valid_rooms:
                    all_rooms = self.branch_data.get('rooms', [])
                    # Exclude shared labs
                    shared_labs = [l.get('name') for l in self.branch_data.get('sharedLabs', [])]
                    legacy_labs = self.branch_data.get('labs', [])
                    
                    forbidden = set(shared_labs + legacy_labs)
                    valid_rooms = [r for r in all_rooms if r not in forbidden]

                for room in valid_rooms:
                    # Check if room is available
                    if not self.state.is_room_available(room, day, slot_index):
                        continue
                    
                    # Create candidate
                    candidate = {
                        'day': day,
                        'slot': slot_index,
                        'year': year,
                        'division': division,
                        'subject': subject_name,
                        'teacher': teacher_name,
                        'room': room,
                        'type': 'Lecture',
                        'batch': None,
                        'score': self._calculate_candidate_score(
                            subject_name, teacher_name, day, slot_index, year, division
                        )
                    }
                    
                    candidates.append(candidate)
        
        return candidates
    
    def _generate_practical_candidates(self, slot_info):
        """
        Generate practical candidates.
        Use LabScheduler for practicals. This is just a fallback/empty.
        """
        return []
    
    # _generate_practical_candidates is now handled by LabScheduler (Hard Constraints)
    # Keeping this simple strictly for safety, but it should return empty
    # as we don't want backtracking to place random practicals.

    
    def _calculate_candidate_score(self, subject, teacher, day, slot_index, year, division):
        """
        Calculate soft constraint penalty score for a candidate.
        
        Lower score = better candidate
        """
        score = 0
        
        # Check teacher load for this day
        teacher_daily_slots = sum(
            1 for (t, d, s) in self.state.teacher_assignments.keys()
            if t == teacher and d == day
        )
        # Penalize if teacher already has many slots this day
        if teacher_daily_slots >= 4:
            score += 5
        elif teacher_daily_slots >= 3:
            score += 2
        
        # Check if same subject already appears today for this division
        same_subject_today = any(
            slot.get('subject') == subject and 
            slot.get('day') == day and
            slot.get('year') == year and
            slot.get('division') == division
            for slot in self.state.slots
        )
        if same_subject_today:
            score += 3  # Penalize subject repetition
        
        # Prefer morning slots for practicals
        if slot_index >= 6:  # Late slots
            score += 1
        
        return score

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
        
        for subject_data in subjects:
            if (subject_data.get('year') != year or 
                subject_data.get('division') != division):
                continue
            
            subject_name = subject_data.get('name')
            
            # Check if we need more lectures for this subject
            remaining = self.state.get_remaining_lectures(subject_name, year, division)
            if remaining <= 0:
                continue
            
            # Find available teachers for this subject
            teachers = self.smart_input.get('teachers', [])
            
            for teacher_data in teachers:
                teacher_name = teacher_data.get('name')
                
                # Check if teacher teaches this subject  
                teacher_subjects = teacher_data.get('subjects', [])
                if subject_name not in teacher_subjects:
                    # If no subjects specified, assume can teach any
                    if teacher_subjects:
                        continue
                
                # Check if teacher is available
                if not self.state.is_teacher_available(teacher_name, day, slot_index):
                    continue
                
                # Find available rooms
                rooms = self.branch_data.get('rooms', [])
                
                for room in rooms:
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
        """Generate practical candidates (all batches synchronized)"""
        candidates = []
        day = slot_info['day']
        slot_index = slot_info['slot']
        year = slot_info['year']
        division = slot_info['division']
        
        # Get practical subjects
        subjects = self.smart_input.get('subjects', [])
        
        for subject_data in subjects:
            if (subject_data.get('year') != year or 
                subject_data.get('division') != division or
                subject_data.get('type') != 'Practical'):
                continue
            
            subject_name = subject_data.get('name')
            num_batches = subject_data.get('batches', 3)
            
            # Check if we need practicals for this subject
            # (Practicals count towards lecturesPerWeek)
            remaining = self.state.get_remaining_lectures(subject_name, year, division)
            if remaining <= 0:
                continue
            
            # Find teacher for practical
            teachers = self.smart_input.get('teachers', [])
            available_teachers = []
            
            for teacher_data in teachers:
                teacher_name = teacher_data.get('name')
                teacher_subjects = teacher_data.get('subjects', [])
                
                if not teacher_subjects or subject_name in teacher_subjects:
                    if self.state.is_teacher_available(teacher_name, day, slot_index):
                        available_teachers.append(teacher_name)
            
            if not available_teachers:
                continue
            
            # Find enough available labs
            labs = self.branch_data.get('labs', [])
            available_labs = [
                lab for lab in labs 
                if self.state.is_room_available(lab, day, slot_index)
            ]
            
            if len(available_labs) < num_batches:
                continue  # Not enough labs
            
            # Create synchronized practical candidate
            for teacher_name in available_teachers:
                # Assign labs to batches
                batch_assignments = []
                for i in range(num_batches):
                    batch_name = f"B{i+1}"
                    lab = available_labs[i]
                    
                    batch_assignments.append({
                        'day': day,
                        'slot': slot_index,
                        'year': year,
                        'division': division,
                        'subject': subject_name,
                        'teacher': teacher_name,
                        'room': lab,
                        'type': 'Practical',
                        'batch': batch_name
                    })
                
                # Calculate score for the entire practical
                score = self._calculate_candidate_score(
                    subject_name, teacher_name, day, slot_index, year, division
                )
                
                # Return as single candidate (but represents multiple slots)
                candidates.append({
                    'practical_group': True,
                    'assignments': batch_assignments,
                    'score': score
                })
        
        return candidates
    
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

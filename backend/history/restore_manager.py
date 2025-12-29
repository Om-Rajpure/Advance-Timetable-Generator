"""
Restore Manager Module

Handles safe restoration of timetable versions with validation.
"""

from typing import Dict, List, Optional, Any
from .version_store import VersionStore


class RestoreManager:
    """Manages safe restoration of timetable versions"""
    
    def __init__(self, version_store: Optional[VersionStore] = None):
        """
        Initialize restore manager.
        
        Args:
            version_store: Version store instance (creates new if None)
        """
        self.version_store = version_store or VersionStore()
    
    def restore_version(
        self,
        branch_id: str,
        version_id: str,
        current_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Restore a timetable version with validation.
        
        Args:
            branch_id: ID of the branch
            version_id: ID of the version to restore
            current_context: Current branch and smart input context
        
        Returns:
            Result dictionary with success status, timetable, and validation info
        """
        # Load the version
        version = self.version_store.get_version(branch_id, version_id)
        
        if not version:
            return {
                'success': False,
                'error': 'Version not found',
                'canRestore': False
            }
        
        timetable = version['timetableSnapshot']
        
        # Validate the restored timetable against current context
        validation = self.validate_restored_timetable(timetable, current_context)
        
        if not validation['valid']:
            return {
                'success': False,
                'error': 'Restored timetable is not compatible with current constraints',
                'canRestore': False,
                'validation': validation,
                'version': {
                    'versionId': version['versionId'],
                    'timestamp': version['timestamp'],
                    'action': version['action'],
                    'description': version['description']
                }
            }
        
        # If validation passes, return success
        return {
            'success': True,
            'canRestore': True,
            'timetable': timetable,
            'version': {
                'versionId': version['versionId'],
                'timestamp': version['timestamp'],
                'action': version['action'],
                'description': version['description'],
                'qualityScore': version['qualityScore']
            },
            'validation': validation
        }
    
    def validate_restored_timetable(
        self,
        timetable: List[Dict],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a restored timetable against current context.
        
        Checks:
        - All teachers still exist
        - All rooms still exist
        - All subjects still exist
        - Basic constraint compliance
        
        Args:
            timetable: Timetable to validate
            context: Current context (branchData, smartInputData)
        
        Returns:
            Validation result with warnings and errors
        """
        warnings = []
        errors = []
        
        # Extract current context data
        smart_input = context.get('smartInputData', {})
        branch_data = context.get('branchData', {})
        
        # Get current teachers, subjects, rooms
        current_teachers = {t['name'] for t in smart_input.get('teachers', [])}
        current_subjects = {s['name'] for s in smart_input.get('subjects', [])}
        current_rooms = set(smart_input.get('rooms', []))
        
        # Validate each slot
        missing_teachers = set()
        missing_subjects = set()
        missing_rooms = set()
        
        for slot in timetable:
            teacher = slot.get('teacher')
            subject = slot.get('subject')
            room = slot.get('room')
            
            # Check teacher
            if teacher and teacher not in current_teachers:
                missing_teachers.add(teacher)
            
            # Check subject
            if subject and subject not in current_subjects:
                missing_subjects.add(subject)
            
            # Check room
            if room and room not in current_rooms:
                missing_rooms.add(room)
        
        # Generate warnings/errors
        if missing_teachers:
            errors.append({
                'type': 'MISSING_TEACHERS',
                'message': f"Teachers no longer exist: {', '.join(sorted(missing_teachers))}",
                'severity': 'HARD'
            })
        
        if missing_subjects:
            errors.append({
                'type': 'MISSING_SUBJECTS',
                'message': f"Subjects no longer exist: {', '.join(sorted(missing_subjects))}",
                'severity': 'HARD'
            })
        
        if missing_rooms:
            warnings.append({
                'type': 'MISSING_ROOMS',
                'message': f"Rooms no longer exist: {', '.join(sorted(missing_rooms))}",
                'severity': 'SOFT'
            })
        
        # Check if timetable structure matches current branch
        current_years = branch_data.get('academicYears', [])
        current_divisions = branch_data.get('divisions', {})
        
        for slot in timetable:
            year = slot.get('year')
            division = slot.get('division')
            
            if year and year not in current_years:
                errors.append({
                    'type': 'INVALID_YEAR',
                    'message': f"Year {year} no longer exists in branch structure",
                    'severity': 'HARD'
                })
                break
            
            if year and division and division not in current_divisions.get(year, []):
                errors.append({
                    'type': 'INVALID_DIVISION',
                    'message': f"Division {division} no longer exists for year {year}",
                    'severity': 'HARD'
                })
                break
        
        # Determine if restoration is valid
        valid = len(errors) == 0
        
        return {
            'valid': valid,
            'warnings': warnings,
            'errors': errors,
            'message': 'Validation passed' if valid else 'Validation failed - see errors'
        }
    
    def compare_versions(
        self,
        branch_id: str,
        version_id_1: str,
        version_id_2: str
    ) -> Dict[str, Any]:
        """
        Compare two versions and generate a diff report.
        
        Args:
            branch_id: ID of the branch
            version_id_1: First version ID
            version_id_2: Second version ID
        
        Returns:
            Comparison report with changes
        """
        version1 = self.version_store.get_version(branch_id, version_id_1)
        version2 = self.version_store.get_version(branch_id, version_id_2)
        
        if not version1 or not version2:
            return {
                'success': False,
                'error': 'One or both versions not found'
            }
        
        # Generate diff
        diff = self._generate_diff(
            version1['timetableSnapshot'],
            version2['timetableSnapshot']
        )
        
        return {
            'success': True,
            'version1': {
                'versionId': version1['versionId'],
                'timestamp': version1['timestamp'],
                'action': version1['action'],
                'qualityScore': version1['qualityScore']
            },
            'version2': {
                'versionId': version2['versionId'],
                'timestamp': version2['timestamp'],
                'action': version2['action'],
                'qualityScore': version2['qualityScore']
            },
            'diff': diff
        }
    
    def _generate_diff(
        self,
        timetable1: List[Dict],
        timetable2: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate a diff between two timetables.
        
        Args:
            timetable1: First timetable
            timetable2: Second timetable
        
        Returns:
            Diff summary
        """
        # Create slot lookup by ID
        slots1 = {s['id']: s for s in timetable1}
        slots2 = {s['id']: s for s in timetable2}
        
        # Find changes
        added = []
        removed = []
        modified = []
        
        # Check for removed and modified slots
        for slot_id, slot1 in slots1.items():
            if slot_id not in slots2:
                removed.append(slot1)
            elif slot1 != slots2[slot_id]:
                modified.append({
                    'id': slot_id,
                    'before': slot1,
                    'after': slots2[slot_id]
                })
        
        # Check for added slots
        for slot_id, slot2 in slots2.items():
            if slot_id not in slots1:
                added.append(slot2)
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified,
            'summary': {
                'addedCount': len(added),
                'removedCount': len(removed),
                'modifiedCount': len(modified),
                'totalChanges': len(added) + len(removed) + len(modified)
            }
        }

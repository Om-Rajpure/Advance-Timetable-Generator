"""
Version Store Module

Handles storage and retrieval of timetable versions.
Versions are stored as JSON files in data/versions/{branch_id}/ directory.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any


class VersionStore:
    """Manages timetable version storage and retrieval"""
    
    def __init__(self, base_dir: str = 'data/versions'):
        """
        Initialize version store.
        
        Args:
            base_dir: Base directory for version storage
        """
        self.base_dir = base_dir
        self._ensure_base_dir()
    
    def _ensure_base_dir(self):
        """Ensure base directory exists"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
    
    def _get_branch_dir(self, branch_id: str) -> str:
        """Get directory path for a specific branch"""
        branch_dir = os.path.join(self.base_dir, branch_id)
        if not os.path.exists(branch_dir):
            os.makedirs(branch_dir)
        return branch_dir
    
    def _get_version_path(self, branch_id: str, version_id: str) -> str:
        """Get file path for a specific version"""
        branch_dir = self._get_branch_dir(branch_id)
        return os.path.join(branch_dir, f"{version_id}.json")
    
    def create_version(
        self,
        branch_id: str,
        timetable: List[Dict],
        action: str,
        description: str,
        metadata: Optional[Dict] = None,
        created_by: str = "System"
    ) -> Dict[str, Any]:
        """
        Create a new timetable version.
        
        Args:
            branch_id: ID of the branch
            timetable: Timetable snapshot (list of slots)
            action: Action type (Generation, Optimization, Manual Edit, Simulation Applied, Restore)
            description: Human-readable description
            metadata: Additional metadata
            created_by: User who created the version
        
        Returns:
            Version object with all metadata
        """
        version_id = f"v_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now().isoformat()
        
        # Compute quality score
        quality_score = self._compute_quality_score(timetable)
        
        # Build metadata
        if metadata is None:
            metadata = {}
        
        metadata.update({
            'slotCount': len(timetable),
            'divisions': list(set(slot.get('division', '') for slot in timetable)),
            'years': list(set(slot.get('year', '') for slot in timetable))
        })
        
        # Create version object
        version = {
            'versionId': version_id,
            'branchId': branch_id,
            'timestamp': timestamp,
            'action': action,
            'description': description,
            'qualityScore': quality_score,
            'createdBy': created_by,
            'timetableSnapshot': timetable,
            'metadata': metadata
        }
        
        # Save to file
        version_path = self._get_version_path(branch_id, version_id)
        with open(version_path, 'w') as f:
            json.dump(version, f, indent=2)
        
        return version
    
    def get_version(self, branch_id: str, version_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific version.
        
        Args:
            branch_id: ID of the branch
            version_id: ID of the version
        
        Returns:
            Version object or None if not found
        """
        version_path = self._get_version_path(branch_id, version_id)
        
        if not os.path.exists(version_path):
            return None
        
        try:
            with open(version_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading version {version_id}: {e}")
            return None
    
    def list_versions(
        self,
        branch_id: str,
        limit: int = 50,
        action_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all versions for a branch.
        
        Args:
            branch_id: ID of the branch
            limit: Maximum number of versions to return
            action_filter: Optional filter by action type
        
        Returns:
            List of version objects (without full timetable snapshots)
        """
        branch_dir = self._get_branch_dir(branch_id)
        
        if not os.path.exists(branch_dir):
            return []
        
        versions = []
        
        # Load all version files
        for filename in os.listdir(branch_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(branch_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    version = json.load(f)
                
                # Apply action filter if specified
                if action_filter and version.get('action') != action_filter:
                    continue
                
                # Create lightweight version object (without full snapshot)
                lightweight_version = {
                    'versionId': version['versionId'],
                    'branchId': version['branchId'],
                    'timestamp': version['timestamp'],
                    'action': version['action'],
                    'description': version['description'],
                    'qualityScore': version['qualityScore'],
                    'createdBy': version['createdBy'],
                    'metadata': version['metadata']
                }
                
                versions.append(lightweight_version)
            
            except Exception as e:
                print(f"Error loading version file {filename}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        versions.sort(key=lambda v: v['timestamp'], reverse=True)
        
        # Apply limit
        return versions[:limit]
    
    def delete_version(self, branch_id: str, version_id: str) -> bool:
        """
        Delete a version.
        
        Args:
            branch_id: ID of the branch
            version_id: ID of the version
        
        Returns:
            True if deleted, False if not found
        """
        version_path = self._get_version_path(branch_id, version_id)
        
        if not os.path.exists(version_path):
            return False
        
        try:
            os.remove(version_path)
            return True
        except Exception as e:
            print(f"Error deleting version {version_id}: {e}")
            return False
    
    def get_latest_version(self, branch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent version for a branch.
        
        Args:
            branch_id: ID of the branch
        
        Returns:
            Latest version object or None
        """
        versions = self.list_versions(branch_id, limit=1)
        if versions:
            version_id = versions[0]['versionId']
            return self.get_version(branch_id, version_id)
        return None
    
    def _compute_quality_score(self, timetable: List[Dict]) -> float:
        """
        Compute a simple quality score for the timetable.
        
        This is a lightweight calculation. For full constraint validation,
        use the ConstraintEngine.
        
        Args:
            timetable: Timetable to score
        
        Returns:
            Quality score (0-100)
        """
        if not timetable:
            return 0.0
        
        # Simple heuristics:
        # - Penalize empty slots
        # - Reward balanced distribution
        # - Check for basic conflicts
        
        total_slots = len(timetable)
        non_empty_slots = len([s for s in timetable if s.get('subject') and s.get('teacher')])
        
        # Basic score based on filled slots
        fill_ratio = non_empty_slots / total_slots if total_slots > 0 else 0
        base_score = fill_ratio * 100
        
        # This is a placeholder - in production, integrate with ConstraintEngine
        return round(base_score, 2)

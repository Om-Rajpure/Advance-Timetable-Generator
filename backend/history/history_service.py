"""
History Service Module

Business logic layer for history operations.
Provides high-level functions for version management.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from .version_store import VersionStore
from .restore_manager import RestoreManager


class HistoryService:
    """High-level history service for version management"""
    
    def __init__(
        self,
        version_store: Optional[VersionStore] = None,
        restore_manager: Optional[RestoreManager] = None
    ):
        """
        Initialize history service.
        
        Args:
            version_store: Version store instance
            restore_manager: Restore manager instance
        """
        self.version_store = version_store or VersionStore()
        self.restore_manager = restore_manager or RestoreManager(self.version_store)
    
    def auto_create_version(
        self,
        timetable: List[Dict],
        context: Dict[str, Any],
        action: str,
        description: str = None,
        created_by: str = "System"
    ) -> Dict[str, Any]:
        """
        Automatically create a version (called by other modules).
        
        Args:
            timetable: Timetable snapshot
            context: Context with branchData and smartInputData
            action: Action type
            description: Optional description (auto-generated if None)
            created_by: User who triggered the action
        
        Returns:
            Created version object
        """
        # Extract branch ID
        branch_data = context.get('branchData', {})
        branch_id = branch_data.get('id')
        
        if not branch_id:
            raise ValueError("Branch ID not found in context")
        
        # Auto-generate description if not provided
        if not description:
            description = self._generate_description(action, timetable, context)
        
        # Extract metadata
        metadata = self._extract_metadata(timetable, context)
        
        # Create version
        version = self.version_store.create_version(
            branch_id=branch_id,
            timetable=timetable,
            action=action,
            description=description,
            metadata=metadata,
            created_by=created_by
        )
        
        return version
    
    def get_version_timeline(
        self,
        branch_id: str,
        limit: int = 50,
        action_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get formatted version timeline for UI display.
        
        Args:
            branch_id: ID of the branch
            limit: Maximum number of versions
            action_filter: Optional filter by action type
        
        Returns:
            Timeline data with versions and statistics
        """
        versions = self.version_store.list_versions(
            branch_id=branch_id,
            limit=limit,
            action_filter=action_filter
        )
        
        # Calculate statistics
        stats = self._calculate_timeline_stats(versions)
        
        # Format versions for UI
        formatted_versions = []
        for v in versions:
            formatted_versions.append({
                'versionId': v['versionId'],
                'timestamp': v['timestamp'],
                'timestampFormatted': self._format_timestamp(v['timestamp']),
                'action': v['action'],
                'actionBadge': self._get_action_badge(v['action']),
                'description': v['description'],
                'qualityScore': v['qualityScore'],
                'qualityLevel': self._get_quality_level(v['qualityScore']),
                'createdBy': v['createdBy'],
                'metadata': v['metadata']
            })
        
        return {
            'versions': formatted_versions,
            'stats': stats,
            'totalCount': len(versions)
        }
    
    def generate_diff_summary(
        self,
        branch_id: str,
        version_id_old: str,
        version_id_new: str
    ) -> Dict[str, Any]:
        """
        Generate a human-readable change summary between versions.
        
        Args:
            branch_id: ID of the branch
            version_id_old: Older version ID
            version_id_new: Newer version ID
        
        Returns:
            Formatted diff summary
        """
        comparison = self.restore_manager.compare_versions(
            branch_id=branch_id,
            version_id_1=version_id_old,
            version_id_2=version_id_new
        )
        
        if not comparison['success']:
            return comparison
        
        diff = comparison['diff']
        
        # Generate human-readable summary
        changes_description = []
        
        if diff['summary']['addedCount'] > 0:
            changes_description.append(f"{diff['summary']['addedCount']} slots added")
        
        if diff['summary']['removedCount'] > 0:
            changes_description.append(f"{diff['summary']['removedCount']} slots removed")
        
        if diff['summary']['modifiedCount'] > 0:
            changes_description.append(f"{diff['summary']['modifiedCount']} slots modified")
        
        summary_text = ", ".join(changes_description) if changes_description else "No changes"
        
        # Calculate quality score change
        score_change = comparison['version2']['qualityScore'] - comparison['version1']['qualityScore']
        score_direction = "improved" if score_change > 0 else "decreased" if score_change < 0 else "unchanged"
        
        return {
            'success': True,
            'version1': comparison['version1'],
            'version2': comparison['version2'],
            'diff': diff,
            'summaryText': summary_text,
            'qualityChange': {
                'delta': round(score_change, 2),
                'direction': score_direction,
                'from': comparison['version1']['qualityScore'],
                'to': comparison['version2']['qualityScore']
            }
        }
    
    def _generate_description(
        self,
        action: str,
        timetable: List[Dict],
        context: Dict[str, Any]
    ) -> str:
        """Generate auto-description based on action"""
        descriptions = {
            'Generation': f"Full timetable generated with {len(timetable)} slots",
            'Optimization': f"Timetable optimized ({len(timetable)} slots)",
            'Manual Edit': "Manual edits saved",
            'Simulation Applied': "What-If simulation applied",
            'Restore': "Previous version restored",
            'Auto-Fix': "Auto-fix applied to resolve conflicts"
        }
        return descriptions.get(action, f"{action} completed")
    
    def _extract_metadata(
        self,
        timetable: List[Dict],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract metadata from timetable and context"""
        metadata = {
            'slotCount': len(timetable),
            'divisions': list(set(slot.get('division', '') for slot in timetable if slot.get('division'))),
            'years': list(set(slot.get('year', '') for slot in timetable if slot.get('year'))),
            'teachers': list(set(slot.get('teacher', '') for slot in timetable if slot.get('teacher'))),
            'subjects': list(set(slot.get('subject', '') for slot in timetable if slot.get('subject')))
        }
        return metadata
    
    def _calculate_timeline_stats(self, versions: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics from version timeline"""
        if not versions:
            return {
                'totalVersions': 0,
                'actionBreakdown': {},
                'averageQuality': 0
            }
        
        action_counts = {}
        quality_scores = []
        
        for v in versions:
            action = v['action']
            action_counts[action] = action_counts.get(action, 0) + 1
            quality_scores.append(v['qualityScore'])
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            'totalVersions': len(versions),
            'actionBreakdown': action_counts,
            'averageQuality': round(avg_quality, 2),
            'latestQuality': quality_scores[0] if quality_scores else 0
        }
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format ISO timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%b %d, %Y – %I:%M %p")
        except:
            return timestamp
    
    def _get_action_badge(self, action: str) -> Dict[str, str]:
        """Get badge styling for action type"""
        badges = {
            'Generation': {'color': 'blue', 'icon': '⚙️'},
            'Optimization': {'color': 'green', 'icon': '📈'},
            'Manual Edit': {'color': 'orange', 'icon': '✏️'},
            'Simulation Applied': {'color': 'purple', 'icon': '🔬'},
            'Restore': {'color': 'gray', 'icon': '🔄'},
            'Auto-Fix': {'color': 'teal', 'icon': '🔧'}
        }
        return badges.get(action, {'color': 'gray', 'icon': '📝'})
    
    def _get_quality_level(self, score: float) -> str:
        """Get quality level label"""
        if score >= 90:
            return 'Excellent'
        elif score >= 75:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        else:
            return 'Needs Improvement'

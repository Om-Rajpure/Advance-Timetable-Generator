"""
Tests for History & Version Control Module

Run with: python -m pytest backend/test_history.py -v
"""

import pytest
import json
import os
import sys

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from history.version_store import VersionStore
from history.restore_manager import RestoreManager
from history.history_service import HistoryService


# Test data
SAMPLE_BRANCH_DATA = {
    'id': 'test-branch-1',
    'branchName': 'Computer Engineering',
    'academicYears': ['SE', 'TE', 'BE'],
    'divisions': {
        'SE': ['A', 'B'],
        'TE': ['A'],
        'BE': ['A']
    }
}

SAMPLE_SMART_INPUT = {
    'teachers': [
        {'id': 't1', 'name': 'Prof. Smith'},
        {'id': 't2', 'name': 'Prof. Johnson'}
    ],
    'subjects': [
        {'id': 's1', 'name': 'Data Structures'},
        {'id': 's2', 'name': 'Algorithms'}
    ],
    'rooms': ['R101', 'R102', 'Lab1']
}

SAMPLE_TIMETABLE = [
    {
        'id': 'slot1',
        'day': 'Monday',
        'time': '9:00',
        'year': 'SE',
        'division': 'A',
        'subject': 'Data Structures',
        'teacher': 'Prof. Smith',
        'room': 'R101'
    },
    {
        'id': 'slot2',
        'day': 'Monday',
        'time': '10:00',
        'year': 'SE',
        'division': 'A',
        'subject': 'Algorithms',
        'teacher': 'Prof. Johnson',
        'room': 'R102'
    }
]


@pytest.fixture
def version_store():
    """Create a version store with temp directory"""
    store = VersionStore(base_dir='data/test_versions')
    yield store
    # Cleanup
    import shutil
    if os.path.exists('data/test_versions'):
        shutil.rmtree('data/test_versions')


@pytest.fixture
def restore_manager(version_store):
    """Create restore manager"""
    return RestoreManager(version_store)


@pytest.fixture
def history_service(version_store, restore_manager):
    """Create history service"""
    return HistoryService(version_store, restore_manager)


def test_create_version(version_store):
    """Test version creation"""
    version = version_store.create_version(
        branch_id='test-branch-1',
        timetable=SAMPLE_TIMETABLE,
        action='Generation',
        description='Test version creation',
        created_by='Test'
    )
    
    assert version is not None
    assert 'versionId' in version
    assert version['action'] == 'Generation'
    assert version['description'] == 'Test version creation'
    assert len(version['timetableSnapshot']) == 2
    assert version['metadata']['slotCount'] == 2


def test_get_version(version_store):
    """Test version retrieval"""
    # Create version
    created_version = version_store.create_version(
        branch_id='test-branch-1',
        timetable=SAMPLE_TIMETABLE,
        action='Generation',
        description='Test version'
    )
    
    # Retrieve version
    retrieved_version = version_store.get_version(
        branch_id='test-branch-1',
        version_id=created_version['versionId']
    )
    
    assert retrieved_version is not None
    assert retrieved_version['versionId'] == created_version['versionId']
    assert len(retrieved_version['timetableSnapshot']) == 2


def test_list_versions(version_store):
    """Test version listing"""
    # Create multiple versions
    v1 = version_store.create_version(
        branch_id='test-branch-1',
        timetable=SAMPLE_TIMETABLE,
        action='Generation',
        description='Version 1'
    )
    
    v2 = version_store.create_version(
        branch_id='test-branch-1',
        timetable=SAMPLE_TIMETABLE,
        action='Optimization',
        description='Version 2'
    )
    
    # List all versions
    versions = version_store.list_versions(branch_id='test-branch-1')
    
    assert len(versions) == 2
    assert versions[0]['versionId'] == v2['versionId']  # Newest first
    assert versions[1]['versionId'] == v1['versionId']
    
    # List with filter
    gen_versions = version_store.list_versions(
        branch_id='test-branch-1',
        action_filter='Generation'
    )
    
    assert len(gen_versions) == 1
    assert gen_versions[0]['action'] == 'Generation'


def test_restore_validation_success(restore_manager):
    """Test successful restore validation"""
    # Create version
    store = restore_manager.version_store
    version = store.create_version(
        branch_id='test-branch-1',
        timetable=SAMPLE_TIMETABLE,
        action='Generation',
        description='Test version'
    )
    
    # Prepare context
    context = {
        'branchData': SAMPLE_BRANCH_DATA,
        'smartInputData': SAMPLE_SMART_INPUT
    }
    
    # Validate restore
    result = restore_manager.restore_version(
        branch_id='test-branch-1',
        version_id=version['versionId'],
        current_context=context
    )
    
    assert result['success'] is True
    assert result['canRestore'] is True
    assert len(result['timetable']) == 2


def test_restore_validation_missing_teacher(restore_manager):
    """Test restore validation with missing teacher"""
    # Create version
    store = restore_manager.version_store
    version = store.create_version(
        branch_id='test-branch-1',
        timetable=SAMPLE_TIMETABLE,
        action='Generation',
        description='Test version'
    )
    
    # Prepare context with missing teacher
    modified_input = SAMPLE_SMART_INPUT.copy()
    modified_input['teachers'] = [{'id': 't1', 'name': 'Prof. Smith'}]  # Remove Johnson
    
    context = {
        'branchData': SAMPLE_BRANCH_DATA,
        'smartInputData': modified_input
    }
    
    # Validate restore
    result = restore_manager.restore_version(
        branch_id='test-branch-1',
        version_id=version['versionId'],
        current_context=context
    )
    
    assert result['success'] is False
    assert result['canRestore'] is False
    assert len(result['validation']['errors']) > 0


def test_compare_versions(restore_manager):
    """Test version comparison"""
    # Create two versions
    store = restore_manager.version_store
    
    v1 = store.create_version(
        branch_id='test-branch-1',
        timetable=SAMPLE_TIMETABLE[:1],  # Only first slot
        action='Generation',
        description='Version 1'
    )
    
    v2 = store.create_version(
        branch_id='test-branch-1',
        timetable=SAMPLE_TIMETABLE,  # Both slots
        action='Manual Edit',
        description='Version 2'
    )
    
    # Compare versions
    comparison = restore_manager.compare_versions(
        branch_id='test-branch-1',
        version_id_1=v1['versionId'],
        version_id_2=v2['versionId']
    )
    
    assert comparison['success'] is True
    assert comparison['diff']['summary']['addedCount'] == 1
    assert comparison['diff']['summary']['totalChanges'] == 1


def test_history_service_auto_create(history_service):
    """Test auto version creation via history service"""
    context = {
        'branchData': SAMPLE_BRANCH_DATA,
        'smartInputData': SAMPLE_SMART_INPUT
    }
    
    version = history_service.auto_create_version(
        timetable=SAMPLE_TIMETABLE,
        context=context,
        action='Generation'
    )
    
    assert version is not None
    assert 'versionId' in version
    assert version['action'] == 'Generation'


def test_version_timeline(history_service):
    """Test version timeline formatting"""
    context = {
        'branchData': SAMPLE_BRANCH_DATA,
        'smartInputData': SAMPLE_SMART_INPUT
    }
    
    # Create multiple versions
    history_service.auto_create_version(
        timetable=SAMPLE_TIMETABLE,
        context=context,
        action='Generation'
    )
    
    history_service.auto_create_version(
        timetable=SAMPLE_TIMETABLE,
        context=context,
        action='Optimization'
    )
    
    # Get timeline
    timeline = history_service.get_version_timeline(
        branch_id='test-branch-1'
    )
    
    assert 'versions' in timeline
    assert 'stats' in timeline
    assert timeline['totalCount'] == 2
    assert timeline['stats']['totalVersions'] == 2
    assert 'actionBreakdown' in timeline['stats']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

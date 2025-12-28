"""
State Cloning Utilities

Provides deep cloning of timetable and context data to ensure
simulations don't modify the original data.
"""

import copy


def clone_timetable(timetable):
    """
    Create a deep copy of timetable data.
    
    Args:
        timetable: List of slot dictionaries
        
    Returns:
        Independent deep copy of timetable
    """
    if not timetable:
        return []
    
    return copy.deepcopy(timetable)


def clone_context(context):
    """
    Create a deep copy of context data (branchData, smartInputData, etc.)
    
    Args:
        context: Dictionary containing branchData, smartInputData, and other config
        
    Returns:
        Independent deep copy of context
    """
    if not context:
        return {}
    
    return copy.deepcopy(context)


def create_simulation_state(timetable, context):
    """
    Create a complete isolated simulation state.
    
    Args:
        timetable: Current timetable
        context: Current context
        
    Returns:
        {
            "timetable": cloned timetable,
            "context": cloned context,
            "original_fingerprint": hash of original data (for verification)
        }
    """
    cloned_timetable = clone_timetable(timetable)
    cloned_context = clone_context(context)
    
    # Create fingerprint for verification
    original_fingerprint = {
        "timetable_slot_count": len(timetable) if timetable else 0,
        "branch_id": context.get('branchData', {}).get('id', 'unknown'),
        "timestamp": None  # Could add timestamp if needed
    }
    
    return {
        "timetable": cloned_timetable,
        "context": cloned_context,
        "original_fingerprint": original_fingerprint
    }


def verify_isolation(original, cloned):
    """
    Verify that cloned data is truly independent from original.
    
    Args:
        original: Original data structure
        cloned: Cloned data structure
        
    Returns:
        True if isolation is verified, False otherwise
    """
    # Check that they're not the same object in memory
    if original is cloned:
        return False
    
    # For lists, check nested objects
    if isinstance(original, list) and isinstance(cloned, list):
        if len(original) != len(cloned):
            return True  # Different lengths = isolated
        
        for o_item, c_item in zip(original, cloned):
            if isinstance(o_item, (dict, list)):
                if o_item is c_item:
                    return False  # Same reference = not isolated
    
    # For dicts, check nested values
    if isinstance(original, dict) and isinstance(cloned, dict):
        for key in original:
            if key in cloned:
                o_val = original[key]
                c_val = cloned[key]
                if isinstance(o_val, (dict, list)):
                    if o_val is c_val:
                        return False  # Same reference = not isolated
    
    return True

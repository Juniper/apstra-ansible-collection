# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

def compare_and_update(current, desired, changes):
    """
    Recursively compare and update the current state to match the desired state.
    
    :param current: The current state dictionary.
    :param desired: The desired state dictionary.
    :param changes: A dictionary to track changes.
    :return: True if any changes were made, False otherwise.
    """
    changed = False
    for key, desired_value in desired.items():
        if key not in current:
            raise ValueError(f"Field '{key}' is missing in the current state.")
        
        current_value = current[key]
        
        if isinstance(desired_value, dict) and isinstance(current_value, dict):
            # Recursively compare nested dictionaries
            nested_changes = {}
            nested_changed = compare_and_update(current_value, desired_value, nested_changes)
            if nested_changed:
                changes[key] = nested_changes
                changed = True
        elif isinstance(desired_value, list) and isinstance(current_value, list):
            # Compare lists
            if current_value != desired_value:
                current[key] = desired_value
                changes[key] = desired_value
                changed = True
        elif current_value != desired_value:
            # Update the current state and track the change
            current[key] = desired_value
            changes[key] = desired_value
            changed = True
    
    return changed
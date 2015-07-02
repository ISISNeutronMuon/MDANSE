def has_parent(window, target):
        
    if window == target:
        return True

    if window.TopLevelParent == window:
        return False

    return has_parent(window.Parent, target)    

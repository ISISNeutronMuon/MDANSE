def has_parent(window, target):
        
    if window == target:
        return True
    else:        
        return has_parent(window.Parent, target)    

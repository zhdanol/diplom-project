def strtobool(val):
    """
    Convert a string representation of truth to True or False.
    
    True values are 'y', 'yes', 't', 'true', 'on', and '1'
    False values are 'n', 'no', 'f', 'false', 'off', and '0'
    
    Raises ValueError if 'val' is anything else.
    """
    if isinstance(val, bool):
        return val
    
    val = str(val).strip().lower()
    
    if val in ('y', 'yes', 't', 'true', 'on', '1', 'true', 'yes', 'enable', 'enabled'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0', 'false', 'no', 'disable', 'disabled'):
        return False
    else:
        raise ValueError(f"invalid truth value: {val}")
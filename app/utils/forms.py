def parse_form(form_data):
    """
    Parse a complete form into a structured object where array notations
    like 'variables[0][name]' become nested dictionaries/lists.
    
    Args:
        form_data: Flask request.form object
        
    Returns:
        A dictionary with all form data structured naturally
    """
    result = {}
    
    # First collect all array-like entries
    arrays = {}
    
    for key in form_data:
        # Handle array notation like variables[0][name]
        if '[' in key and ']' in key:
            parts = []
            current = ""
            in_bracket = False
            
            # Parse the key into parts, respecting nested brackets
            for char in key:
                if char == '[':
                    if current:
                        parts.append(current)
                        current = ""
                    in_bracket = True
                elif char == ']':
                    if current:
                        parts.append(current)
                        current = ""
                    in_bracket = False
                else:
                    current += char
            
            if current:
                parts.append(current)
            
            # Handle the parsed parts
            if len(parts) >= 2:
                prefix = parts[0]
                
                # Initialize arrays structure if needed
                if prefix not in arrays:
                    arrays[prefix] = {}
                
                # Build the nested structure
                current_level = arrays[prefix]
                for i, part in enumerate(parts[1:-1]):
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]
                
                # Set the value at the leaf level
                current_level[parts[-1]] = form_data[key]
        else:
            # Regular form field
            result[key] = form_data[key]
    
    # Now convert nested dict structure to proper arrays where needed
    for prefix, data in arrays.items():
        # Determine if this is a sequential array (with numeric indices)
        is_sequential = all(idx.isdigit() for idx in data.keys())
        
        if is_sequential:
            # Convert to a properly ordered list
            items = []
            indices = sorted(data.keys(), key=int)
            
            for idx in indices:
                item_data = data[idx]
                
                # Recursively convert nested arrays
                for key, value in list(item_data.items()):
                    if isinstance(value, dict):
                        # Check if this is a sequential array
                        is_nested_sequential = all(idx.isdigit() for idx in value.keys())
                        if is_nested_sequential:
                            # Convert to list
                            nested_items = []
                            nested_indices = sorted(value.keys(), key=int)
                            for nested_idx in nested_indices:
                                nested_items.append(value[nested_idx])
                            item_data[key] = nested_items
                
                items.append(item_data)
            
            result[prefix] = items
        else:
            # Non-sequential array, keep as dictionary
            result[prefix] = data
    
    # Handle checkboxes with 'Y'/'N' convention
    checkbox_fields = ['limitByUser', 'limitDisplay', 'wideDisplay', 'useAjax']
    for field in checkbox_fields:
        if field in result:
            result[field] = 'Y'
        else:
            result[field] = 'N'
    
    return result
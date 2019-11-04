
def nested_get(dict, path_array, default_value=None):
    temp_dict = dict
    for k in path_array:
        temp_dict = temp_dict.get(k, None)
        if temp_dict is None:
            return default_value

    return temp_dict

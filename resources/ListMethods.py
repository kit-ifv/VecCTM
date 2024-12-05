from resources import Settings


def __flatten_list__(_2d_list):
    flat_list = []
    # Iterate through the outer list
    for element in _2d_list:
        if type(element) is list:
            # If the element is of type list, iterate through the sublist
            for item in element:
                flat_list.append(item)
        else:
            flat_list.append(element)
    return flat_list


def __fill_slots__(param_list):
    steps = Settings.get_settings().STEPS
    # single value
    if not type(param_list) == list: return [param_list] * steps

    # multiple values
    newList = [None] * steps

    # convert dict to two seperate lists to work with
    _2d_key = list(map(lambda x: list(x.keys()), param_list))
    key = __flatten_list__(_2d_key)
    _2d_values = list(map(lambda x: list(x.values()), param_list))
    values = __flatten_list__(_2d_values)

    # add end value

    if key[len(key) - 1] > steps: raise IndexError(
        "max given index is " + str(key[len(key) - 1]) + ", but the max step number is " + str(Settings.STEPS))
    key.append(steps)

    # build new list with Settings.STEP entries
    for j in range(1, len(key)):
        for i in range(key[j - 1] - 1, key[j]):
            newList[i] = values[j - 1]

    return newList

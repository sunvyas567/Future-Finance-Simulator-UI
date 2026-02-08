import copy

def apply_scenario_diff(base_data: dict, diff: dict) -> dict:
    scenario = copy.deepcopy(base_data)

    for field, value in diff.items():
        if field in scenario:
            scenario[field]["input"] = value
        else:
            scenario[field] = {"input": value}

    return scenario

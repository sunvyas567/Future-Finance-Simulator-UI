def build_scenario_prompt(base, scenario):
    prompt = "Compare base retirement plan with modified scenario.\n\n"

    prompt += "Base Assumptions:\n"
    for k, v in base.items():
        if isinstance(v, dict) and "input" in v:
            prompt += f"- {k}: {v['input']}\n"

    prompt += "\nScenario Changes:\n"
    for k, v in scenario.items():
        if isinstance(v, dict) and "input" in v:
            prompt += f"- {k}: {v['input']}\n"

    prompt += "\nExplain risks, benefits, and long-term impact."

    return prompt

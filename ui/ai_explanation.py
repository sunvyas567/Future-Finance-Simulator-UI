def explain_scenario(base_df, scenario_df, scenario_name):
    y1_base = base_df.iloc[0]
    y1_scn = scenario_df.iloc[0]

    delta_income = (
        y1_scn["otalIncome"]
        - y1_base["TotalIncome"]
    )

    explanation = f"""
Scenario '{scenario_name}' Analysis:

• Year 1 income difference: {delta_income:,.0f}

"""

    if delta_income > 0:
        explanation += "This scenario improves income due to better yield assumptions or growth."
    else:
        explanation += "This scenario reduces income due to conservative assumptions or higher expenses."

    explanation += "\n\nConsider reviewing inflation, FD rates, and SWP assumptions."

    return explanation

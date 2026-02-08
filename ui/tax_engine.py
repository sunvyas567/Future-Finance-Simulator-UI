from ui.retirement_profiles import RETIREMENT_PROFILES


def compute_post_tax_income(df):
    """
    Generic tax post-processing for all countries
    """
    if "TotalIncome" not in df.columns:
        raise ValueError("TotalIncome not found in projections")

    if "TotalTax" not in df.columns:
        df["TotalTax"] = 0

    df["NetIncomeAfterTax"] = df["TotalIncome"] - df["TotalTax"]
    return df


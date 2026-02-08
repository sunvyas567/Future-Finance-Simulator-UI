import streamlit as st

COUNTRY_MODELS = {
    "India": {
        "currency": "₹",
        "splits": {
            "LocalGroceryVeg": 30,
            "LocalWaterElectricity": 6,
            "LocalTransportFuel": 10,
            "LocalMedicalInsurance": 12,
            "LocalHouseRepairs": 8,
            "LocalEntertainment": 14,
            "LocalMiscellaneousTax": 10
        }
    },
    "USA": {
        "currency": "$",
        "splits": {
            "LocalGroceryVeg": 15,
            "LocalWaterElectricity": 17,
            "LocalTransportFuel": 14,
            "LocalMedicalInsurance": 18,
            "LocalInsuranceVehicle": 6,
            "LocalEntertainment": 10,
            "LocalOthersOpt": 20
        }
    },
    "UK": {
        "currency": "£",
        "splits": {
            "LocalGroceryVeg": 16,
            "LocalWaterElectricity": 14,
            "LocalTransportFuel": 12,
            "LocalMedicalInsurance": 8,
            "LocalPropertyTax": 12,
            "LocalEntertainment": 14,
            "LocalOthersOpt": 24
        }
    }
}


def render_expense_auto_distribution(user_data: dict, user: dict):
    st.subheader("🌍 Smart Expense Setup")
    st.caption("Automatically distribute expenses based on country norms")

    country = st.selectbox(
        "Country Profile",
        options=list(COUNTRY_MODELS.keys())
    )

    model = COUNTRY_MODELS[country]
    currency = model["currency"]

    monthly_total = st.number_input(
        f"Total Monthly Household Expense ({currency})",
        min_value=0.0,
        value=60000.0
    )

    st.markdown("### Auto-Distribution Preview")

    updated_values = {}

    for field, pct in model["splits"].items():
        amount = monthly_total * (pct / 100)
        updated_values[field] = amount

        col1, col2 = st.columns([3, 1])
        col1.markdown(f"{field}")
        col2.metric(f"{pct}%", f"{amount:,.0f}")

    if st.button("✅ Apply to Detailed Expenses"):
        for k, v in updated_values.items():
            user_data[k] = {"input": v}
        st.success("Expenses applied successfully")

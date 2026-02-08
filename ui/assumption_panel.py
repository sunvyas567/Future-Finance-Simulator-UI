import streamlit as st


def render_assumption_panel(base_config:list, user_data:dict,user:dict):
    st.subheader("🧠 Assumptions")

    is_guest = user is None

    assumption_fields = [
        f for f in base_config
        if f.get("assumption") is True
    ]

    if not assumption_fields:
        st.info("No assumptions defined for this country.")
        return

    with st.expander("View & Edit Assumptions", expanded=True):
        for item in assumption_fields:
            fname = item["Field Name"]
            label = item["Field Description"]
            default = item.get("Field Default Value", 0)

            # Initialize once
            if fname not in user_data:
                user_data[fname] = {"input": default}

            value = user_data[fname]["input"]

            # Normalize numeric
            try:
                value = float(value)
            except:
                pass

            user_data[fname]["input"] = st.number_input(
                label,
                value=value,
                disabled=is_guest
            )

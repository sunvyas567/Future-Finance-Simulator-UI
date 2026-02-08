import streamlit as st

def render_advisor_panel(advice: dict):
    st.subheader("🧠 Advisor Insights")

    if not advice or not isinstance(advice, dict):
        st.info("Advisor insights unavailable.")
        return

    has_any_content = False

    # -----------------------------
    # SUMMARY
    # -----------------------------
    summary = advice.get("summary")
    if summary:
        has_any_content = True
        st.markdown(f"**Summary:** {summary}")

    # -----------------------------
    # POSITIVES
    # -----------------------------
    positives = advice.get("positives", [])
    if positives:
        has_any_content = True
        with st.expander("✅ What’s Working Well"):
            for p in positives:
                st.success(p)

    # -----------------------------
    # WARNINGS
    # -----------------------------
    warnings = advice.get("warnings", [])
    if warnings:
        has_any_content = True
        with st.expander("⚠️ Warnings"):
            for w in warnings:
                st.warning(w)

    # -----------------------------
    # RECOMMENDATIONS
    # -----------------------------
    recs = advice.get("recommendations", [])
    if recs:
        has_any_content = True
        with st.expander("📌 Recommendations"):
            for r in recs:
                st.info(r)

    # -----------------------------
    # FALLBACK (ONLY if truly empty)
    # -----------------------------
    if not has_any_content:
        st.info("Advisor insights unavailable for this scenario.")

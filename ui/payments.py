import streamlit as st
import time
from services.api_client import create_payment_order, get_entitlement


def render_payments(username: str):
    st.header("🚀 Upgrade to Premium")

    st.markdown(
        """
        Unlock powerful features:
        - Unlimited projections
        - PDF report downloads
        - AI advisor & scenarios
        """
    )

    plans = {
        "monthly": {
            "label": "Monthly Plan",
            "price": "₹299 / month",
            "desc": "Pay monthly, cancel anytime"
        },
        "lifetime": {
            "label": "Lifetime Plan",
            "price": "₹11,700 one-time",
            "desc": "One-time payment, lifetime access"
        }
    }

    selected_plan = st.radio(
        "Choose a plan",
        options=list(plans.keys()),
        format_func=lambda k: f"{plans[k]['label']} — {plans[k]['price']}"
    )

    # Prevent duplicate orders
    if "payment_in_progress" not in st.session_state:
        st.session_state.payment_in_progress = False

    if st.button("Proceed to Payment", disabled=st.session_state.payment_in_progress):
        st.session_state.payment_in_progress = True

        with st.spinner("Creating secure payment order..."):
            try:
                order = create_payment_order(username, selected_plan)
            except Exception as e:
                st.error(f"Could not create payment order: {e}")
                st.session_state.payment_in_progress = False
                return

        order_id = order["order_id"]
        amount = order["amount"]
        currency = order["currency"]
        razorpay_key = order["razorpay_key"]

        st.success("Payment order created")

        checkout_html = f"""
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        <script>
            var options = {{
                "key": "{razorpay_key}",
                "amount": "{amount}",
                "currency": "{currency}",
                "name": "Future Finance Simulator",
                "description": "{plans[selected_plan]['label']}",
                "order_id": "{order_id}",
                "theme": {{
                    "color": "#0ea5e9"
                }}
            }};
            var rzp = new Razorpay(options);
            rzp.open();
        </script>
        """

        st.components.v1.html(checkout_html, height=520)

        st.info("After completing payment, please wait for confirmation...")

        # ---- Poll entitlement (UX only; webhook is authority) ----
        for _ in range(30):
            time.sleep(2)
            entitlement = get_entitlement(username)

            if entitlement.get("is_premium"):
                st.success("🎉 Payment confirmed! Premium activated.")
                st.balloons()

                # Reset state
                st.session_state.payment_in_progress = False
                st.session_state.view = "app"
                st.rerun()

        st.warning(
            "Payment not confirmed yet.\n\n"
            "If you've paid, it may take a few seconds to reflect. "
            "You can safely refresh this page."
        )

        st.session_state.payment_in_progress = False

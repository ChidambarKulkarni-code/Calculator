import streamlit as st
import pandas as pd

# ----------------------
# PAGE CONFIG
# ----------------------
st.set_page_config(page_title="Premium Calculator", layout="wide")

# ----------------------
# HEADER
# ----------------------
st.title("📊 Premium Calculator")
st.markdown("A simple and professional tool to calculate premiums with clarity.")

# ----------------------
# SIDEBAR INPUTS
# ----------------------
st.sidebar.header("Input Parameters")

with st.sidebar.form("calc_form"):
    age = st.number_input("Age", min_value=18, max_value=100, value=30)
    tenure = st.number_input("Tenure (years)", min_value=1, max_value=40, value=10)
    base_amount = st.number_input("Base Amount", min_value=1000, value=100000)

    submit = st.form_submit_button("Calculate")

# ----------------------
# INSTRUCTIONS
# ----------------------
st.subheader("ℹ️ How to Use")
st.info("Enter age, tenure, and base amount in the sidebar, then click Calculate.")

# ----------------------
# CALCULATION LOGIC
# ----------------------
def calculate_premium(age, tenure, base_amount):
    age_factor = 1 + (age - 30) * 0.01
    tenure_factor = 1 + tenure * 0.02
    premium = base_amount * age_factor * tenure_factor
    return premium, age_factor, tenure_factor

# ----------------------
# OUTPUT
# ----------------------
if submit:
    if age <= 0 or tenure <= 0 or base_amount <= 0:
        st.error("All inputs must be greater than zero.")
    else:
        with st.spinner("Calculating..."):
            premium, age_factor, tenure_factor = calculate_premium(age, tenure, base_amount)

        st.success("Calculation Complete")

        col1, col2, col3 = st.columns(3)

        col1.metric("Age Factor", f"{age_factor:.2f}")
        col2.metric("Tenure Factor", f"{tenure_factor:.2f}")
        col3.metric("Premium", f"₹{premium:,.2f}")

        st.subheader("📖 Calculation Breakdown")
        st.write(f"Premium = Base Amount × Age Factor × Tenure Factor")
        st.write(f"= {base_amount} × {age_factor:.2f} × {tenure_factor:.2f}")
        st.write(f"= ₹{premium:,.2f}")

        # ----------------------
        # DOWNLOAD OPTION
        # ----------------------
        df = pd.DataFrame({
            "Age": [age],
            "Tenure": [tenure],
            "Base Amount": [base_amount],
            "Premium": [premium]
        })

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Results",
            data=csv,
            file_name="premium_calculation.csv",
            mime="text/csv"
        )

# ----------------------
# FOOTER
# ----------------------
st.markdown("---")
st.caption("Built with Streamlit • Improved UX version")

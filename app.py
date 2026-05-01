import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from io import BytesIO

# --------------------------------------------------
# Fixed backend rate file
# --------------------------------------------------
RATE_FILE = Path("data/Main GCL Rates.xlsx")

PRODUCT_SHEETS = {
    ("Home Loan", "Level Cover"): "Home Loan Level Cover",
    ("Home Loan", "Reducing Cover"): "Home Loan Reducing Cover",

    ("Personal Loan", "Level Cover"): "Personal Loan Level Cover",
    ("Personal Loan", "Reducing Cover"): "Personal Loan Reducing Cover",

    ("Loan Against Property", "Level Cover"): "Lap Level Cover",
    ("Loan Against Property", "Reducing Cover"): "Lap Reducing",

    ("Secured Business Loan", "Level Cover"): "Secured Loan Business Level",
    ("Secured Business Loan", "Reducing Cover"): "Secured Loan Business Reducing",

    ("Unsecured Business Loan", "Level Cover"): "Unsecured Loan Business Level",
    ("Unsecured Business Loan", "Reducing Cover"): "Unsecured Loan Business Reducin",

    ("Micro Loan", "Level Cover"): "Micro Loan Level Cover",
    ("Micro Loan", "Reducing Cover"): "Micro Loan Reducing",
}

REQUIRED_COLUMNS = [
    "Customer Name",
    "Age",
    "Loan Amount",
    "Tenure Months"
]

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="GCL Premium Calculator",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------
# Header
# --------------------------------------------------
st.title("Group Credit Life Premium Calculator")
st.caption(
    "Bulk premium calculation engine using fixed age-wise and tenure-wise GCL rate tables."
)

st.divider()

# --------------------------------------------------
# Helper Functions
# --------------------------------------------------
@st.cache_data
def load_rate_table(sheet_name):
    raw = pd.read_excel(
        RATE_FILE,
        sheet_name=sheet_name,
        header=None
    )

    header_matches = raw[
        raw.iloc[:, 0].astype(str).str.strip().eq("Entry Age")
    ].index

    if len(header_matches) == 0:
        raise ValueError(f"'Entry Age' header not found in sheet: {sheet_name}")

    header_row = header_matches[0]

    tenures = (
        raw.iloc[header_row, 1:]
        .dropna()
        .astype(float)
        .astype(int)
        .tolist()
    )

    table = raw.iloc[
        header_row + 1:,
        :len(tenures) + 1
    ].dropna(how="all")

    table = table.rename(columns={0: "Entry Age"})
    table.columns = ["Entry Age"] + tenures
    table = table.dropna(subset=["Entry Age"])

    for tenure in tenures:
        table[tenure] = pd.to_numeric(
            table[tenure],
            errors="coerce"
        )

    return table


def find_age_band(age, age_bands):
    for band in age_bands:
        text = str(band).strip()

        if "-" in text:
            low, high = text.split("-")

            if int(low) <= age <= int(high):
                return band

        else:
            if int(float(text)) == age:
                return band

    return None


def get_rate(rate_table, age, tenure):
    tenure_cols = [
        col for col in rate_table.columns
        if col != "Entry Age"
    ]

    if tenure not in tenure_cols:
        return None, f"Tenure {tenure} months not available in rate table."

    ages_available = rate_table["Entry Age"].tolist()

    if any("-" in str(age_value) for age_value in ages_available):
        matched_age = find_age_band(age, ages_available)
    else:
        matched_age = age if age in ages_available else None

    if matched_age is None:
        return None, f"Age {age} not available in rate table."

    rate = rate_table.loc[
        rate_table["Entry Age"].astype(str) == str(matched_age),
        tenure
    ].iloc[0]

    if pd.isna(rate):
        return None, "Rate is blank in the rate table."

    return float(rate), "Rate found"


def calculate_premium(row, rate_table):
    try:
        age = int(row["Age"])
        loan_amount = float(row["Loan Amount"])
        tenure = int(row["Tenure Months"])

    except Exception:
        return pd.Series([
            np.nan,
            np.nan,
            "Invalid age / loan amount / tenure"
        ])

    rate, remark = get_rate(
        rate_table,
        age,
        tenure
    )

    if rate is None:
        return pd.Series([
            np.nan,
            np.nan,
            remark
        ])

    premium = (loan_amount / 100000) * rate

    return pd.Series([
        rate,
        round(premium, 2),
        "Calculated"
    ])


def convert_df_to_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Premium Output"
        )

    output.seek(0)

    return output


def read_uploaded_file(uploaded_file):
    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded_file)
    else:
        return pd.read_excel(uploaded_file)


# --------------------------------------------------
# Rate file availability check
# --------------------------------------------------
if not RATE_FILE.exists():
    st.error(
        "Rate file not found. Please keep the file at: data/Main GCL Rates.xlsx"
    )
    st.stop()

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
st.sidebar.title("Calculator Settings")

product = st.sidebar.selectbox(
    "Select Product Type",
    sorted(set([key[0] for key in PRODUCT_SHEETS.keys()]))
)

available_covers = [
    cover
    for prod, cover in PRODUCT_SHEETS.keys()
    if prod == product
]

cover_type = st.sidebar.selectbox(
    "Select Cover Type",
    available_covers
)

sheet_name = PRODUCT_SHEETS[(product, cover_type)]

st.sidebar.success(f"Selected Rate Sheet: {sheet_name}")

st.sidebar.divider()

st.sidebar.markdown("### Premium Formula")
st.sidebar.code("Premium = (Loan Amount / 100000) × Rate Per Lakh")

# --------------------------------------------------
# Main layout
# --------------------------------------------------
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("Upload Customer File")

    uploaded_file = st.file_uploader(
        "Upload Excel or CSV file",
        type=["xlsx", "xls", "csv"]
    )

with right_col:
    st.subheader("Required Columns")

    st.write("Your upload file must contain:")

    for col in REQUIRED_COLUMNS:
        st.markdown(f"- `{col}`")

    st.info(
        "Extra columns such as Loan Account Number, Branch, Mobile Number, etc. will be retained."
    )

# --------------------------------------------------
# Processing section
# --------------------------------------------------
if uploaded_file is not None:

    try:
        customer_df = read_uploaded_file(uploaded_file)
    except Exception as e:
        st.error(f"Could not read uploaded file: {e}")
        st.stop()

    st.divider()

    st.subheader("Uploaded File Preview")
    st.dataframe(
        customer_df.head(20),
        use_container_width=True
    )

    missing_cols = [
        col for col in REQUIRED_COLUMNS
        if col not in customer_df.columns
    ]

    if missing_cols:
        st.error(
            f"Missing required columns: {', '.join(missing_cols)}"
        )

    else:
        st.success("File uploaded successfully. Required columns are available.")

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Uploaded Records", len(customer_df))
        c2.metric("Product Type", product)
        c3.metric("Cover Type", cover_type)

        st.divider()

        if st.button("Calculate Premium", type="primary"):

            try:
                rate_table = load_rate_table(sheet_name)
            except Exception as e:
                st.error(f"Could not load rate table: {e}")
                st.stop()

            output_df = customer_df.copy()

            output_df[[
                "Rate Per Lakh",
                "Calculated Premium",
                "Remarks"
            ]] = output_df.apply(
                lambda row: calculate_premium(row, rate_table),
                axis=1
            )

            total_records = len(output_df)
            calculated_records = (
                output_df["Remarks"] == "Calculated"
            ).sum()
            failed_records = total_records - calculated_records
            total_premium = output_df[
                "Calculated Premium"
            ].sum(skipna=True)

            st.success("Premium calculation completed successfully.")

            m1, m2, m3, m4 = st.columns(4)

            m1.metric("Total Records", total_records)
            m2.metric("Calculated Records", calculated_records)
            m3.metric("Failed Records", failed_records)
            m4.metric("Total Premium", f"₹{total_premium:,.2f}")

            st.divider()

            st.subheader("Calculated Premium Output")

            st.dataframe(
                output_df,
                use_container_width=True
            )

            if failed_records > 0:
                st.warning(
                    "Some records could not be calculated. Please check the Remarks column."
                )

            excel_file = convert_df_to_excel(output_df)

            st.download_button(
                label="Download Calculated Premium Excel",
                data=excel_file,
                file_name="gcl_premium_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.info("Upload a customer file to begin calculation.")

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

SHEET_ID = "1umG0zNs4Uz9IqfZXPXEeAgfSWoRTzDDsEwlSRC-3PnM"

st.set_page_config(
    page_title="Treasurer Ledger",
    page_icon="💰",
    layout="centered"
)


# --------------------------------------------------
# GOOGLE SHEETS CONNECTION
# --------------------------------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(SHEET_ID).worksheet("Treasurer_Ledger")
records = sheet.get_all_records()

# --------------------------------------------------
# Calculate Note/Coins Balance
# --------------------------------------------------

if "show_success" not in st.session_state:
    st.session_state.show_success = False

notes_balance = 0.0
coins_balance = 0.0

for row in records:

    method = row["Method"]
    trans_type = row["Transaction Type"]
   
    try:
        amount = float(
            str(row["Amount"])
            .replace("€", "")
            .replace(",", "")
            .strip()
        )
    except:
        amount = 0

    if method == "Cash Notes":

        if trans_type == "Money In":
            notes_balance += amount

        elif trans_type in ["Money Out", "Lodgement"]:
            notes_balance -= amount

    elif method == "Cash Coins":

        if trans_type == "Money In":
            coins_balance += amount

        elif trans_type in ["Money Out", "Lodgement"]:
            coins_balance -= amount

# --------------------------------------------------
# Money Calculation
# --------------------------------------------------

st.title("Current Balance")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Notes on Hand",
        f"€{notes_balance:,.2f}"
    )

with col2:
    st.metric(
        "Coins on Hand",
        f"€{coins_balance:,.2f}"
    )

with col3:
    st.metric(
        "Total Cash",
        f"€{notes_balance + coins_balance:,.2f}"
    )

# --------------------------------------------------
# PAGE
# --------------------------------------------------

st.title("Treasurer Ledger")

st.write(
    "Record cash, cheque, Revolut and Bank transactions."
)

# --------------------------------------------------
# FORM
# --------------------------------------------------

with st.form(
    "ledger_form",
    clear_on_submit=True
):

    name = st.text_input(
        "Name / Payee"
    )

    category = st.selectbox(
        "Category",
        [
            "Supporters Draw",
            "50/50 Draw",
            "Physio",
            "Membership",
            "Equipment",
            "Club Shop",
            "Lodgement",
            "Sponsorship",
            "Other"
        ]
    )

    transaction_type = st.selectbox(
        "Transaction Type",
        [
            "Money In",
            "Money Out",
            "Lodgement",
            "Withdrawel"
        ]
    )

    method = st.selectbox(
        "Method",
        [
            "Cash Notes",
            "Cash Coins",
            "Revolut",
            "BOI",
            "Cheque",
            "Credit Union"
        ]
    )

    amount = st.number_input(
        "Amount (€)",
        min_value=0.0,
        step=0.01,
        format="%.2f"
    )

    cheque_number = st.text_input(
        "Cheque Number (Optional)"
    )

    comments = st.text_area(
        "Comments"
    )

    submit = st.form_submit_button(
        "Save Transaction"
    )

# --------------------------------------------------
# SAVE RECORD
# --------------------------------------------------

if submit:

    if not name.strip():

        st.error(
            "Please enter a Name / Payee."
        )

    elif amount <= 0:

        st.error(
            "Amount must be greater than zero."
        )

    else:

        timestamp = datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        )

        sheet.append_row(
            [
                timestamp,
                name,
                category,
                transaction_type,
                method,
                amount,
                cheque_number,
                comments
            ]
        )

        st.session_state.show_success = True
        st.rerun()

# --------------------------------------------------
# Display success
# --------------------------------------------------
if st.session_state.show_success:

    st.success(
        "✅ Transaction saved successfully."
    )

    st.session_state.show_success = False
# --------------------------------------------------
# ADMIN VIEW
# --------------------------------------------------

st.markdown("---")

admin_pin = st.text_input(
    "Admin PIN",
    type="password"
)

if admin_pin == st.secrets["ADMIN_PIN"]:


    records = sheet.get_all_records()

    df = pd.DataFrame(records)

    # Newest entries first
    df = df.iloc[::-1]

    st.subheader("Treasurer Ledger Entries")

    search = st.text_input(
        "Search Name / Payee"
    )

    if search:

        df = df[
            df["Name / Payee"].astype(str).str.contains(
                search,
                case=False,
                na=False
            )
        ]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Ballymore Treasurer Ledger"
)

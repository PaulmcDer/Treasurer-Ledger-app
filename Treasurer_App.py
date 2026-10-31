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
@st.cache_resource
def get_sheets():

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)

    return {
        "ledger": client.open_by_key(SHEET_ID).worksheet("Treasurer_Ledger"),
        "todo": client.open_by_key(SHEET_ID).worksheet("To_Do"),
        "fifty": client.open_by_key(SHEET_ID).worksheet("50-50")
    }

sheets = get_sheets()

sheet = sheets["ledger"]
todo_sheet = sheets["todo"]
fifty_sheet = sheets["fifty"]

@st.cache_data(ttl=30)
def load_ledger_data():
    return sheet.get_all_records()


@st.cache_data(ttl=30)
def load_todo_data():
    return todo_sheet.get_all_records()


@st.cache_data(ttl=30)
def load_fifty_data():
    return fifty_sheet.get_all_records()

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "show_success" not in st.session_state:
    st.session_state.show_success = False

if "save_pin_ok" not in st.session_state:
    st.session_state.save_pin_ok = False

if "todo_pin_ok" not in st.session_state:
    st.session_state.todo_pin_ok = False

# --------------------------------------------------
# CSS STYLE For Buttons
# --------------------------------------------------
st.markdown("""
<style>

/* ===========================
   STANDARD BUTTONS
   =========================== */

.stButton > button {
    background-color: #FFD300 !important;
    color: #000000 !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: 1px solid #b8860b !important;
}

.stButton > button p {
    color: #000000 !important;
}

.stButton > button:hover {
    background-color: #ffea00 !important;
    color: #000000 !important;
    transform: translateY(-1px);
    transition: 0.2s;
}
/* ===========================
   METRICS
   =========================== */

[data-testid="stMetric"] {
    text-align: center;
    background-color: #FFF8CC;
    border: 1px solid #FFD700;
    border-radius: 10px;
    padding: 10px;
}

[data-testid="stMetric"] *,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    color: #000000 !important;
}

/* ===========================
   TABS
   =========================== */

/* All tabs */
.stTabs [data-baseweb="tab"] {
    min-height: 50px;
    padding: 0 20px;
    color: #555555 !important;
    font-weight: 500 !important;
    border-radius: 8px 8px 0 0;
}

/* Hover */
.stTabs [data-baseweb="tab"]:hover {
    color: #000000 !important;
}

/* ACTIVE TAB */
.stTabs [aria-selected="true"] {
    color: #B8860B !important;      /* Dark gold text */
    font-weight: 800 !important;
}

/* Active tab text */
.stTabs [aria-selected="true"] p {
    color: #B8860B !important;
    font-weight: 800 !important;
}

/* Yellow underline */
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #FFD300 !important;
    height: 4px !important;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Calculate Note/Coins Balance
# --------------------------------------------------

notes_balance = 0.0
coins_balance = 0.0

# Fetch data here 
records = load_ledger_data()

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
# TABS
# --------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "💰 Transactions",
        "🔒 Admin",
        "✅ To Do",
        "🏆 50-50 Payments"
    ]
)

# --------------------------------------------------
# TAB 1 - TRANSACTIONS
# --------------------------------------------------

with tab1:

    st.subheader("Treasurer Ledger")
    st.write("Record cash, cheque, Revolut and Bank transactions.")
    st.markdown("---")

# ----------------------------------------------
# 1️⃣ SAVE TRANSACTION PIN (separate from Admin)
# ----------------------------------------------
    st.markdown("*Save Transaction Pin*")

    save_pin = st.text_input(
        "Enter 4‑digit PIN",
        type="password",
        max_chars=4
    )

    if save_pin == st.secrets["SAVE_PIN"]:
        st.session_state.save_pin_ok = True
        st.success("Save PIN accepted")
    elif save_pin == "":
        st.session_state.save_pin_ok = False
    else:
        st.session_state.save_pin_ok = False
        st.error("Incorrect Save PIN")

        st.markdown("---")

# ----------------------------------------------
# 2️⃣ TRANSACTION FORM (button disabled by PIN)
# ----------------------------------------------

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
            "Save Transaction",
            disabled=not st.session_state.save_pin_ok
        )

# ----------------------------------------------
# 3️⃣ VALIDATION + SAVE LOGIC
# ----------------------------------------------

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

            st.cache_data.clear()
            st.session_state.show_success = True
            st.rerun()

    if st.session_state.show_success:

        st.success(
            "✅ Transaction saved successfully."
        )

        st.session_state.show_success = False

# --------------------------------------------------
# TAB 2 - ADMIN
# --------------------------------------------------

with tab2:

    st.subheader("Treasurer Ledger Admin")

    st.markdown("---")

    admin_pin = st.text_input(
        "Admin PIN",
        type="password"
    )

    if admin_pin == st.secrets["ADMIN_PIN"]:

        st.subheader("Current Balance")

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

        df = pd.DataFrame(records)

        st.subheader(
            "Treasurer Ledger Entries"
        )

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

    elif admin_pin:

        st.error("Incorrect PIN")

# --------------------------------------------------
# TAB 3 - TO DO
# --------------------------------------------------

with tab3:

    st.subheader("✅ Treasurer To Do List")

    st.markdown("---")

    st.markdown("*To Do - Pin*")

    todo_pin = st.text_input(
        "Enter 4-digit PIN",
        type="password",
        max_chars=4,
        key="todo_pin"
    )

    if todo_pin == st.secrets["SAVE_PIN"]:
        st.session_state.todo_pin_ok = True
        st.success("PIN accepted")

    elif todo_pin == "":
        st.session_state.todo_pin_ok = False

    else:
        st.session_state.todo_pin_ok = False
        st.error("Incorrect PIN")

    st.markdown("---")

    with st.form(
        "todo_form",
        clear_on_submit=True
    ):

        todo_description = st.text_input(
            "To Do Item"
        )

        add_todo = st.form_submit_button(
            "➕ Add To Do",
            disabled=not st.session_state.todo_pin_ok
        )

        if add_todo and todo_description.strip():

            todo_sheet.append_row(
                [
                    datetime.now().strftime("%d/%m/%Y"),
                    todo_description,
                    "Pending"
                ]
            )
            st.cache_data.clear()

            st.success(
                "To Do item added."
            )

            st.rerun()

    st.markdown("---")

    if st.session_state.todo_pin_ok:

        todo_records = load_todo_data()

        if todo_records:

            todo_df = pd.DataFrame(todo_records)

            pending_items = todo_df[
                todo_df["Status"] == "Pending"
            ]

            st.subheader("Pending Items")

            st.dataframe(
                pending_items,
                use_container_width=True,
                hide_index=True
            )

            if not pending_items.empty:

                selected_item = st.selectbox(
                    "Select Item Completed",
                    pending_items["Description"]
                )

                complete_item = st.button(
                    "✅ Mark Selected Item Complete"
                )

                if complete_item:

                    cell = todo_sheet.find(
                        selected_item
                    )

                    todo_sheet.update_cell(
                        cell.row,
                        3,
                        "Complete"
                    )

                    st.cache_data.clear()

                    st.success(
                        "Item marked complete."
                    )

                    st.rerun()

# --------------------------------------------------
# TAB 4 - 50-50 PAYMENTS
# --------------------------------------------------

with tab4:

    st.subheader("🏆 50-50 Payments")

    payment_records = load_fifty_data()

    if not payment_records:

        st.info("No payment records found.")

    else:

        payment_df = pd.DataFrame(payment_records)

        pending_df = payment_df[
            payment_df["Status"]
            .astype(str)
            .str.strip()
            .eq("Pending")
        ]

        st.subheader("Pending Payments")

        if pending_df.empty:

            st.success("No pending payments.")

        else:

            st.dataframe(
                pending_df,
                use_container_width=True,
                hide_index=True
            )

            payment_options = [
                f"{row['Winner Name']} | €{row['Jackpot €']} | {row['Ticket Number']}"
                for _, row in pending_df.iterrows()
            ]

            selected_payment = st.selectbox(
                "Select Payment",
                payment_options
            )

            if st.button(
                "✅ Mark Payment Complete",
                key="complete_5050_payment"
            ):

                selected_index = payment_options.index(
                    selected_payment
                )

                selected_row = pending_df.iloc[
                    selected_index
                ]

                sheet_row = (
                    pending_df.index[selected_index]
                    + 2
                )

                fifty_sheet.update_cell(
                    sheet_row,
                    6,
                    "Complete"
                )

                st.cache_data.clear()

                st.success(
                    "Payment marked as complete."
                )

                st.rerun()
                
#---------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Ballymore Treasurer Ledger"
)

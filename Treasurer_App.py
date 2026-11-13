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
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_resource
def get_sheets():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SHEETS_SCOPES,
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(SHEET_ID)

    return {
        "ledger": spreadsheet.worksheet("Treasurer_Ledger"),
        "todo": spreadsheet.worksheet("To_Do"),
        "fifty": spreadsheet.worksheet("50-50"),
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
# APP STYLING
# --------------------------------------------------
st.markdown("""
<style>
    :root {
        --ledger-ink: #172a25;
        --ledger-muted: #65756e;
        --ledger-green: #174b3a;
        --ledger-gold: #e7b84b;
        --ledger-border: #e3e9e4;
        --ledger-surface: #ffffff;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 10% 0%, rgba(231, 184, 75, 0.09), transparent 34rem),
            #f5f7f4;
        color: var(--ledger-ink);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 960px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .ledger-hero {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        overflow: hidden;
        margin-bottom: 0.6rem;
        padding: 1.25rem 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 22px;
        background: linear-gradient(118deg, #123d31 0%, #1d5b44 72%, #286b4d 100%);
        box-shadow: 0 8px 24px rgba(23, 58, 44, 0.10);
        color: #ffffff;
    }

    .ledger-hero::after {
        position: absolute;
        top: -6rem;
        right: 12%;
        width: 18rem;
        height: 18rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 50%;
        box-shadow: 0 0 0 2.5rem rgba(255, 255, 255, 0.035),
                    0 0 0 5rem rgba(255, 255, 255, 0.025);
        content: "";
        pointer-events: none;
    }

    .ledger-kicker {
        margin: 0 0 0.55rem;
        color: #f0cc75;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }

    .ledger-hero h1 {
        margin: 0;
        color: #ffffff;
        font-size: clamp(1.6rem, 4vw, 2rem);
        font-weight: 750;
        letter-spacing: -0.045em;
        line-height: 1.1;
    }

    .ledger-hero p {
        margin: 0.65rem 0 0;
        color: #e0ece5;
        font-size: 0.9rem;
    }

    .ledger-date {
        z-index: 1;
        flex: 0 0 auto;
        padding: 0.8rem 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 14px;
        background: rgba(8, 35, 26, 0.2);
        color: #ffffff;
        font-size: 0.88rem;
        font-weight: 650;
        text-align: center;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.2rem;
        padding: 0.3rem;
        border: 1px solid var(--ledger-border);
        border-radius: 14px;
        background: #ffffff;
    }

    .stTabs [data-baseweb="tab"] {
        min-height: 3.2rem;
        flex: 1 1 0;
        padding: 0 1rem;
        border-radius: 10px;
        color: var(--ledger-muted);
        font-weight: 650;
        transition: color 160ms ease, background 160ms ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--ledger-green);
        background: rgba(23, 75, 58, 0.05);
    }

    .stTabs [aria-selected="true"],
    .stTabs [aria-selected="true"] p {
        color: var(--ledger-green) !important;
        font-weight: 750 !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #edf4ee;
        box-shadow: inset 0 -3px 0 var(--ledger-gold);
    }

    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }

    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1.4rem;
    }

    [data-testid="stForm"],
    [data-testid="stMetric"],
    [data-testid="stDataFrame"] {
        border: 1px solid var(--ledger-border);
        border-radius: 16px;
        background: var(--ledger-surface);
        box-shadow: 0 5px 18px rgba(23, 42, 37, 0.045);
    }

    [data-testid="stForm"] {
        padding: 1.2rem 1.35rem;
    }

    [data-testid="stMetric"] {
        padding: 1rem 1.1rem;
    }

    [data-testid="stMetricLabel"] {
        color: var(--ledger-muted) !important;
        font-weight: 650;
    }

    [data-testid="stMetricValue"] {
        color: var(--ledger-green) !important;
        font-weight: 750;
    }

    .stButton > button,
    [data-testid="stFormSubmitButton"] > button {
        min-height: 2.75rem;
        border: 1px solid #174b3a !important;
        border-radius: 10px !important;
        background: #174b3a !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
    }

    .stButton > button p,
    [data-testid="stFormSubmitButton"] > button p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    .stButton > button:hover:not(:disabled),
    [data-testid="stFormSubmitButton"] > button:hover:not(:disabled) {
        transform: translateY(-1px);
        border-color: #286b4d !important;
        background: #286b4d !important;
        box-shadow: 0 6px 14px rgba(23, 75, 58, 0.18);
    }

    .stButton > button:disabled,
    [data-testid="stFormSubmitButton"] > button:disabled {
        border-color: #c9d2cc !important;
        background: #e5e9e6 !important;
        color: #748078 !important;
    }

    .stButton > button:disabled p,
    [data-testid="stFormSubmitButton"] > button:disabled p {
        color: #526057 !important;
    }

    .stButton > button:focus-visible,
    [data-testid="stFormSubmitButton"] > button:focus-visible,
    [data-baseweb="tab"]:focus-visible {
        outline: 3px solid rgba(231, 184, 75, 0.7);
        outline-offset: 2px;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        border-color: #d7dfd9;
        border-radius: 9px;
        background: #ffffff;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: #287353;
        box-shadow: 0 0 0 2px rgba(40, 115, 83, 0.14);
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    .ledger-footer {
        padding: 0.25rem 0 0.75rem;
        color: var(--ledger-muted);
        font-size: 0.8rem;
        letter-spacing: 0.025em;
        text-align: center;
    }

    @media (prefers-reduced-motion: reduce) {
        .stButton > button,
        [data-testid="stFormSubmitButton"] > button,
        .stTabs [data-baseweb="tab"] {
            transition: none;
            transform: none !important;
        }
    }

    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1rem 1rem 1.5rem;
        }

        .ledger-hero {
            align-items: flex-start;
            flex-direction: column;
            gap: 0.65rem;
            padding: 1rem 1.1rem;
            border-radius: 17px;
        }

        .ledger-date {
            padding: 0;
            border: 0;
            background: transparent;
            font-size: 0.8rem;
            text-align: left;
        }

        .stTabs [data-baseweb="tab"] {
            min-height: 2.9rem;
            padding: 0 0.35rem;
            font-size: 0.82rem;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea {
            font-size: 16px;
        }

        [data-testid="stForm"] {
            padding: 0.9rem;
        }
    }
</style>
""", unsafe_allow_html=True)

st.html(
    f"""
    <header class="ledger-hero">
        <div>
            <div class="ledger-kicker">Ballymore · Treasurer</div>
            <h1>Treasurer ledger</h1>
            <p>Payments, cash and everyday follow-ups.</p>
        </div>
        <div class="ledger-date">{datetime.now().strftime('%a, %d %b %Y')}</div>
    </header>
    """
)

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

tab1, tab3, tab4, tab2, tab5, tab6 = st.tabs(
    [
        "🎫 Entry",
        "✅ To Do",
        "💰 50/50",
        "📖 Ledger",
        "🔧 Tools",
        "📥 Download"
    ]
)

# --------------------------------------------------
# TAB 1 - TRANSACTIONS
# --------------------------------------------------

with tab1:

    st.subheader("Record a transaction")
    st.caption("Add today's income, payment or lodgement to the club ledger.")

# ----------------------------------------------
# 1️⃣ SAVE TRANSACTION PIN (separate from Admin)
# ----------------------------------------------
    st.markdown("#### Unlock transaction entry")
    st.caption("Enter your transaction PIN to enable saving.")

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

# ----------------------------------------------
# 2️⃣ TRANSACTION FORM (button disabled by PIN)
# ----------------------------------------------

    with st.form(
        "ledger_form",
        clear_on_submit=True
    ):

        identity_col, category_col = st.columns([1.25, 1])
        with identity_col:
            name = st.text_input("Name / Payee")
        with category_col:
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

        type_col, method_col = st.columns(2)
        with type_col:
            transaction_type = st.selectbox(
                "Transaction Type",
                [
                    "Money In",
                    "Money Out",
                    "Lodgement",
                    "Withdrawel"
                ]
            )
        with method_col:
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

        with st.expander("Add a note or cheque number"):
            cheque_number = st.text_input("Cheque Number (Optional)")

            comments = st.text_area(
                "Notes (Optional)",
                placeholder="Add a reference or a short note for this entry."
            )

        submit = st.form_submit_button(
            "Save transaction",
            disabled=not st.session_state.save_pin_ok,
            width="stretch"
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
        "6-Digit Admin PIN",
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
            width="stretch",
            hide_index=True
        )

    elif admin_pin:

        st.error("Incorrect PIN")

# --------------------------------------------------
# TAB 3 - TO DO
# --------------------------------------------------

with tab3:

    st.subheader("Tasks")
    st.caption("Add a quick reminder, then mark it complete when it's done.")

    if st.session_state.get("task_success"):
        st.success(st.session_state.pop("task_success"))

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
            "What needs doing?",
            placeholder="e.g. Lodge the weekend's cash"
        )

        add_todo = st.form_submit_button(
            "Add task",
            disabled=not st.session_state.todo_pin_ok,
            width="stretch"
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

            st.session_state.task_success = "Task added."
            st.rerun()

        elif add_todo:
            st.error("Enter a task before saving.")

    st.markdown("---")

    if st.session_state.todo_pin_ok:

        todo_records = load_todo_data()

        if todo_records:

            todo_df = pd.DataFrame(todo_records)

            pending_items = todo_df[
                todo_df["Status"] == "Pending"
            ]

            st.subheader(f"Pending tasks · {len(pending_items)}")

            if pending_items.empty:
                st.success("All caught up. No pending tasks.")

            for row_index, task in pending_items.iterrows():
                with st.container(border=True):
                    st.text(str(task["Description"]))
                    if st.button(
                        "Mark complete",
                        key=f"complete_task_{row_index}",
                        icon=":material/check:",
                        width="stretch",
                    ):
                        todo_sheet.update_cell(int(row_index) + 2, 3, "Complete")
                        load_todo_data.clear()
                        st.session_state.task_success = "Task completed."
                        st.rerun()
        else:
            st.info("No tasks yet. Add your first reminder above.")

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
                width="stretch",
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
                key="complete_5050_payment",
                width="stretch"
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
                
# ==========================================
# # TAB 5 - MAINTENANCE
# ==========================================

with tab5:
    st.subheader("🛠️ Worksheet Maintenance")
    
    # 1. PIN Security Check Section
    st.markdown("**Maintenance access PIN**")
    maint_pin = st.text_input(
        "Enter 4-digit PIN",
        type="password",
        max_chars=4,
        key="maint_pin"
    )

    # Initialize a session state key for this tab's security check if not already present
    if "maint_pin_ok" not in st.session_state:
        st.session_state.maint_pin_ok = False

    # Validate the PIN against your existing SAVE_PIN secret
    if maint_pin == st.secrets["SAVE_PIN"]:
        st.session_state.maint_pin_ok = True
        st.success("PIN accepted. Access granted.")
    elif maint_pin == "":
        st.session_state.maint_pin_ok = False
    else:
        st.session_state.maint_pin_ok = False
        st.error("Incorrect PIN")

    st.markdown("---")

    # 2. Main Tools: Only visible if PIN is confirmed correct
    if st.session_state.maint_pin_ok:
        
        # Dropdown selection now including all 3 sheets
        maintenance_target = st.selectbox(
            "Select Sheet to Manage:",
            options=["Treasurer Ledger", "To Do List", "50-50 Payments"],
            key="maintenance_sheet_select"
        )

        # 3. Assign target variables and dynamic caching clearing based on the 3 selections
        if maintenance_target == "Treasurer Ledger":
            target_sheet = sheet                 # Maps to your ledger variable from your setup
            records = load_ledger_data()         # Maps to your ledger caching function
            cache_clear_func = load_ledger_data.clear
        elif maintenance_target == "To Do List":
            target_sheet = todo_sheet
            records = load_todo_data()
            cache_clear_func = load_todo_data.clear
        else:
            target_sheet = fifty_sheet
            records = load_fifty_data()
            cache_clear_func = load_fifty_data.clear

        # Display data if it exists
        if not records:
            st.info(f"The '{maintenance_target}' sheet contains no entries.")
        else:
            maintenance_df = pd.DataFrame(records)
            
            st.write("### Current Data View")
            st.dataframe(maintenance_df, width="stretch", hide_index=True)

            st.divider()
            st.subheader("🚨 Danger Zone")

            # Preview the last entry row safely
            last_row_num = len(records) + 1
            last_entry = records[-1]

            # 1. Display sticky success message if a deletion just happened
            if "deletion_success_msg" in st.session_state and st.session_state.deletion_success_msg:
                st.success(st.session_state.deletion_success_msg)
                # Clear the message flag so it doesn't show up again on the next normal interaction
                st.session_state.deletion_success_msg = None

            st.error(f"⚠️ **Attention:** The action below will permanently delete row **#{last_row_num}** from **{maintenance_target}**.")
            st.write("**Preview of item to be deleted:**")
            st.json(last_entry)

            # 2. Safety Lock Checkbox
            confirm_delete = st.checkbox(
                f"I am sure I want to permanently delete this row from {maintenance_target}.", 
                key="confirm_delete_checkbox"
            )

            # 3. Delete Action (Button is disabled unless checkbox is checked)
            if st.button(
                f"🗑️ Confirm: Delete Most Recent Entry", 
                key="btn_delete_most_recent", 
                disabled=not confirm_delete
            ):
                with st.spinner("Deleting row from Google Sheets..."):
                    try:
                        target_sheet.delete_rows(last_row_num)
                        
                        # Clear cache immediately so the table updates accurately
                        cache_clear_func()
                        
                        # Store the success message in session state so it survives the st.rerun()
                        st.session_state.deletion_success_msg = f"✅ Successfully deleted row #{last_row_num} from {maintenance_target}!"
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"An error occurred while deleting the row: {e}")

with tab6:
    st.subheader("Export Accounts (Excel)")
    st.caption("Download the Ledger for a financial year (1 October to 30 September).")

    from io import BytesIO

    export_pin = st.text_input(
        "Enter Admin PIN",
        type="password",
        key="export_pin"
    )

    if export_pin and export_pin == st.secrets["ADMIN_PIN"]:

        export_records = load_ledger_data()

        if not export_records:
            st.info("The ledger contains no entries.")
        else:
            export_df = pd.DataFrame(export_records)
            date_col = export_df.columns[0]
            export_df["_parsed"] = pd.to_datetime(
                export_df[date_col],
                format="%d/%m/%Y %H:%M",
                errors="coerce"
            )

            current_year = datetime.now().year
            first_year = (
                int(export_df["_parsed"].min().year) - 1
                if export_df["_parsed"].notna().any()
                else current_year - 1
            )
            start_years = list(range(current_year, first_year - 1, -1))
            if datetime.now().month < 10:
                start_years = [y for y in start_years if y < current_year] or [current_year - 1]

            fin_year = st.selectbox(
                "Financial Year",
                start_years,
                format_func=lambda y: f"{y}/{y + 1}  (1 Oct {y} – 30 Sep {y + 1})"
            )

            start_date = datetime(fin_year, 10, 1)
            end_date = datetime(fin_year + 1, 9, 30, 23, 59, 59)

            year_df = export_df[
                (export_df["_parsed"] >= start_date) &
                (export_df["_parsed"] <= end_date)
            ].sort_values("_parsed").drop(columns="_parsed")

            st.write(f"**{len(year_df)}** entries found.")
            st.dataframe(year_df, width="stretch", hide_index=True)

            if year_df.empty:
                st.warning("No entries in this financial year.")
            else:
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    year_df.to_excel(writer, index=False, sheet_name="Ledger")
                    ws = writer.sheets["Ledger"]
                    for col_cells in ws.columns:
                        width = max(len(str(c.value or "")) for c in col_cells) + 2
                        ws.column_dimensions[col_cells[0].column_letter].width = min(width, 50)

                st.download_button(
                    "📥 Download Excel",
                    data=buffer.getvalue(),
                    file_name=f"Ledger_{fin_year}-{fin_year + 1}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch"
                )
    elif export_pin:
        st.error("Incorrect PIN")


#---------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.html('<footer class="ledger-footer">Ballymore · Treasurer ledger</footer>')

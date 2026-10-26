
import pandas as pd
import streamlit as st
import plotly.express as px
from ingest_documents import ingest_document
from workflow import graph
from database import (
    DB_PATH,
    save_sales_data,
    load_sales_data,
    get_revenue_by_region,
)

from analytics import (
    calculate_total_revenue,
    calculate_total_profit,
    revenue_by_month,
)


st.set_page_config(
    page_title="InsightPilot",
    page_icon="📊",
    layout="wide",
)

st.title("InsightPilot")
st.caption("AI-powered Business Intelligence Assistant")


# Track the CSV uploader so it can be reset
if "uploader_version" not in st.session_state:
    st.session_state.uploader_version = 0

if "dataset_source" not in st.session_state:
    st.session_state.dataset_source = "Saved database dataset"


def create_sample_data():
    """Create the default sample sales dataset."""
    data = {
        "month": [
            "2026-01", "2026-01", "2026-02",
            "2026-02", "2026-03", "2026-03",
        ],
        "region": [
            "North", "South", "North",
            "South", "North", "South",
        ],
        "product": [
            "Laptop", "Phone", "Laptop",
            "Phone", "Laptop", "Phone",
        ],
        "revenue": [12000, 9000, 10000, 11000, 8000, 13000],
        "cost": [8000, 6000, 7000, 7000, 5500, 8000],
    }

    df = pd.DataFrame(data)
    df["month"] = pd.to_datetime(df["month"])
    df["profit"] = df["revenue"] - df["cost"]

    return df


def reset_to_sample_data():
    """Replace the saved dataset with sample data."""
    sample_df = create_sample_data()
    save_sales_data(sample_df)

    st.session_state.dataset_source = "Sample data"
    st.session_state.uploader_version += 1


# Sidebar controls
st.sidebar.header("Sales Data")

st.sidebar.button(
    "Reset to sample data",
    on_click=reset_to_sample_data,
    use_container_width=True,
)

uploaded_file = st.sidebar.file_uploader(
    "Upload a sales CSV",
    type=["csv"],
    key=f"sales_csv_{st.session_state.uploader_version}",
)


# Load uploaded data, saved data, or sample data
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        required_columns = [
            "month", "region", "product", "revenue", "cost"
        ]

        missing_columns = [
            col for col in required_columns
            if col not in df.columns
        ]

        if missing_columns:
            st.error(
                "Missing required columns: "
                + ", ".join(missing_columns)
            )
            st.stop()

        if df.empty:
            st.error("The uploaded CSV contains no records.")
            st.stop()

        df["month"] = pd.to_datetime(
            df["month"], errors="coerce"
        )

        for col in ["revenue", "cost"]:
            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            )

        if df[required_columns].isnull().any().any():
            st.error(
                "Required columns contain missing or invalid values."
            )
            st.stop()

        for col in ["region", "product"]:
            df[col] = df[col].astype(str).str.strip()

            if df[col].eq("").any():
                st.error(f"Empty values found in '{col}'.")
                st.stop()

        df["profit"] = df["revenue"] - df["cost"]

        # Persist the validated dataset
        save_sales_data(df)
        st.session_state.dataset_source = uploaded_file.name

    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as error:
        st.error(f"Could not read the CSV: {error}")
        st.stop()

    except Exception as error:
        st.error(f"Could not process the CSV: {error}")
        st.stop()

elif DB_PATH.exists():
    df = load_sales_data()

else:
    df = create_sample_data()
    save_sales_data(df)
    st.session_state.dataset_source = "Sample data"


# Ensure derived values are consistent
df["month"] = pd.to_datetime(df["month"])
df["profit"] = df["revenue"] - df["cost"]


# Show the active dataset
st.caption(
    f"Currently loaded dataset: {st.session_state.dataset_source}"
)


# KPI cards
total_revenue = calculate_total_revenue(df)
total_profit = calculate_total_profit(df)

col1, col2, col3 = st.columns(3)

col1.metric("Total Revenue", f"${total_revenue:,.2f}")
col2.metric("Total Profit", f"${total_profit:,.2f}")
col3.metric("Sales Records", len(df))


# Monthly revenue chart
st.subheader("Monthly Revenue")

monthly = revenue_by_month(df)

fig = px.line(
    monthly,
    x="month",
    y="revenue",
    markers=True,
    title="Revenue Trend",
)

st.plotly_chart(fig, use_container_width=True)


# Regional revenue using SQL
st.subheader("Revenue by Region")

regional = get_revenue_by_region()

st.bar_chart(
    regional,
    x="region",
    y="total_revenue",
)


# Product revenue using Pandas
st.subheader("Revenue by Product")

product_revenue = (
    df.groupby("product", as_index=False)["revenue"]
    .sum()
    .sort_values("revenue", ascending=False)
)

st.bar_chart(
    product_revenue,
    x="product",
    y="revenue",
)


# Detailed records
st.subheader("Sales Records")
st.dataframe(df, use_container_width=True)



# -------------------------------
# Business Document Upload
# -------------------------------

st.header("Upload Business Documents")

st.write(
    "Upload PDF or TXT business reports to make them "
    "available for questions in InsightPilot."
)

uploaded_file = st.file_uploader(
    "Choose a business document",
    type=["pdf", "txt"],
    key="business_document_uploader",
)

if uploaded_file is not None:
    st.write(f"Selected file: **{uploaded_file.name}**")

    if st.button("Index Document", key="index_business_document"):
        try:
            with st.spinner(
                "Extracting text and indexing document..."
            ):
                result = ingest_document(
                    filename=uploaded_file.name,
                    file_bytes=uploaded_file.getvalue(),
                )

            st.success(
                f"Successfully indexed {result['filename']}. "
                f"Created {result['chunks_stored']} text chunks."
            )

        except Exception as error:
            st.error(
                f"Could not index document: "
                f"{type(error).__name__}: {error}"
            )


# -----------------------------
# InsightPilot AI Assistant
# -----------------------------

st.divider()
st.header("Ask InsightPilot")
st.write(
    "Ask questions about your sales data and business reports."
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display previous messages.
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept a new question.
question = st.chat_input("Ask a business question...")

if question:
    st.session_state.chat_history.append({
        "role": "user",
        "content": question,
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("InsightPilot is analyzing your question..."):
            try:
                result = graph.invoke({
                    "question": question,
                    "answer": "",
                    "route": "",
                })

                answer = result["answer"]
                st.markdown(answer)

                # Show which route handled the question.
                st.caption(f"Route used: {result['route']}")

            except Exception as error:
                answer = (
                    "Sorry, I couldn't process that question. "
                    "Please try again."
                )
                st.error(answer)
                print(f"InsightPilot error: {type(error).__name__}: {error}")

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer,
    })

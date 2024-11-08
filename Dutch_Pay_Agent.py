import time
import streamlit as st
import pandas as pd
from datetime import date, datetime
from pyparsing import empty


def calculate_dutch_pay(df):
    cols_lst = df.columns.tolist()
    names_lst = list(set(cols_lst) - set(["date", "name", "price"]))
    for name in names_lst:
        df[name] = df[name].fillna(False)

    result_df = pd.DataFrame()
    for idx, row in df.iterrows():
        participants_lst = list()
        for name in names_lst:
            if row[name] == False:
                participants_lst.append(name)

        participants_num = len(participants_lst)
        divided_amount = round(row.price / participants_num)
        part_result_df = pd.DataFrame(
            {
                "from": participants_lst,
                "to": [row["name"]] * participants_num,
                "price": [divided_amount] * participants_num,
            }
        )
        result_df = pd.concat([result_df, part_result_df], ignore_index=True)

    result_df["is_same"] = result_df["from"] == result_df["to"]
    result_df = result_df[result_df.is_same == False]
    result_df.reset_index(drop=True, inplace=True)
    del result_df["is_same"]

    result_df = result_df.groupby(["from", "to"], as_index=False)["price"].sum()
    result_df.sort_values(by=["from", "to", "price"], ascending=True)
    return result_df


@st.cache_data
def get_csv(df):
    return df.to_csv().encode(
        "utf-8"
    )  # IMPORTANT: Cache the conversion to prevent computation on every rerun


# Initialization
st.set_page_config(page_title="Dutch Pay Agent", page_icon="💸", layout="wide")
if "enter_names" not in st.session_state:
    st.session_state["enter_names"] = False
if "enter_price" not in st.session_state:
    st.session_state["enter_price"] = False
PROGRESS_BAR_SECONDS = 1.5

empty_L, main_site, empty_R = st.columns([0.3, 1.0, 0.3])
with empty_L:
    empty()
with empty_R:
    empty()

with main_site:
    # title
    st.title("Dutch Pay Agent💸")
    st.divider()

    # step 1. enter the names
    st.subheader("STEP 1. Enter the names")
    st.markdown("Enter the names of everyone who participated in the Dutch pay.")
    names_str = st.text_area(
        "(Enter one name per line.)", placeholder="ex: Alex\nJamie\nTaylor"
    )
    names_lst = sorted(list(set(names_str.split("\n"))))

    if st.button("OK", key="bt1"):
        st.session_state["enter_names"] = True
        people_num = len(names_lst)
        st.write(f"{people_num} names have been entered.")
    st.divider()

    # step 2. enter the payment details
    if st.session_state["enter_names"] == True:
        st.subheader("STEP 2. Enter the payment details & Check the participants.")
        st.markdown("Please enter the payment information.")
        st.markdown(
            "And please activate the checkbox for those who did not participate in splitting the bill for each payment."
        )

        format_dict = {"date": [date(2024, 1, 1)], "name": "Gildong Hong", "price": [0]}
        for name_col in names_lst:
            format_dict[name_col] = False
        format_df = pd.DataFrame(format_dict)

        return_df = st.data_editor(
            format_df,
            column_config={
                "date": st.column_config.DateColumn(
                    "Date",
                    help="(Optional) Please enter the payment date.",
                    min_value=date(2024, 1, 1),
                    max_value=date(2099, 12, 31),
                    format="YYYY-MM-DD",
                    step=1,
                    required=False,
                ),
                "name": st.column_config.SelectboxColumn(
                    "Payer's name",
                    help="(Required) Please select the name of the person who made the payment.",
                    width="medium",
                    options=names_lst,
                    required=True,
                ),
                "price": st.column_config.NumberColumn(
                    "Price",
                    help="(Required) Please enter only the numeric value of the payment amount.",
                    min_value=0,
                    step=1,
                    format="%d",
                    required=True,
                ),
            },
            # hide_index=True,
            num_rows="dynamic",
        )

        if st.button("OK", key="bt2"):
            st.session_state["enter_price"] = True
        st.divider()

    # step 3. calculate
    if st.session_state["enter_price"] == True:
        placeholder = st.empty()
        for i in range(0, 110, 10):
            placeholder.progress(i, "Wait for it...")
            time.sleep(PROGRESS_BAR_SECONDS / 10)
        placeholder.markdown("Done!")

        st.subheader("Result")
        st.markdown(
            """Please inform the person listed in the "from" column to transfer the amount specified in the "price" column to the person listed in the "to" column."""
        )

        result_df = calculate_dutch_pay(return_df)
        st.dataframe(result_df)

        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S")
        csv = get_csv(result_df)
        st.download_button(
            label="Download result as CSV",
            data=csv,
            file_name=f"Dutch_Pay_Agent_result_{formatted_datetime}.csv",
            mime="text/csv",
        )

        st.image("bmc_qr.png", caption="Buy me a coffee☕", output_format="PNG")

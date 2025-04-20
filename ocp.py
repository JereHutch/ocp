"""
Jeremiah Hutchison
Program Name: ocproject.py
Description: A program to take an excel datasheet and give the savings potential
for contracts that overlap each other. We will be using streamlit and pandas
for the framework and manipulation of the data. 
"""

#We'll be using Streamlit as the framework and Pandas for the dataframes.
import streamlit as st
import pandas as pd

#Let's Show the TITLE!!
st.set_page_config(page_title="Contract Overlap Analyzer", layout="wide")
st.title("Contract Overlap Analyzer")
st.write("Welcome! To Begin, Upload an Excel file with your contract data.")
st.write("Required Columns: Contract_Name, Contract_ID, Service_Type, Start_Date, End_Date, Cost, Maintenance")

#Upload their Excel File with their contract data.
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

#Define the function for grouping overlapping contracts.
def assign_overlap_groups(df):
    df = df.copy()
    #Convert the date data into ACTUAL objects.
    df["Start_Date"] = pd.to_datetime(df["Start_Date"])
    df["End_Date"] = pd.to_datetime(df["End_Date"])
    df = df.sort_values("Start_Date").reset_index(drop=True)

    #ID's for Overlapping Groups.
    group_id = 0
    current_group = []
    current_end = pd.Timestamp.min
    df["Overlap_Group"] = -1

    #Setup for the overlap on dates.
    for i, row in df.iterrows():
        start = row["Start_Date"]
        end = row["End_Date"]

        if start > current_end:
            if current_group:
                for idx in current_group:
                    df.loc[idx, "Overlap_Group"] = group_id
                group_id += 1
            current_group = [i]
            current_end = end
        else:
            current_group.append(i)
            current_end = max(current_end, end)

    if current_group:
        for idx in current_group:
            df.loc[idx, "Overlap_Group"] = group_id

    return df

#Now we setup the main idea for the project itself. Overlapping by Service Type.
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    #Make sure they have the right columns.
    required_cols = ["Contract_ID", "Service_Type", "Start_Date", "End_Date", "Cost", "Maintenance"]
    if not all(col in df.columns for col in required_cols):
        st.error(f"Missing one or more required columns: {', '.join(required_cols)}")
    else:
        #Calculate the total cost of the contract.
        df["Total Cost"] = df["Cost"] + df["Maintenance"]

        all_grouped = []
        all_savings = []

        #Filter the service types
        service_types = df["Service_Type"].unique()
        selected_types = st.multiselect("Filter by Service Type", service_types, default=service_types)
        df = df[df["Service_Type"].isin(selected_types)]

        #Process each Service Type separately in their own group.
        for service in selected_types:
            st.subheader(f"Service Type: {service}")
            df_service = df[df["Service_Type"] == service].copy()
            df_grouped = assign_overlap_groups(df_service)
            all_grouped.append(df_grouped)

            st.write("Overlapping Contracts:")
            st.dataframe(df_grouped)

            #Calculate those savings.
            savings_list = []
            for group, group_df in df_grouped.groupby("Overlap_Group"):
                if len(group_df) > 1:
                    total_cost = group_df["Total Cost"].sum()
                    min_cost = group_df["Total Cost"].min()
                    savings = total_cost - min_cost

                    savings_list.append({
                        "Service_Type": service,
                        "Overlap_Group": group,
                        "Total Group Cost": total_cost,
                        "Minimum Contract Total Cost": min_cost,
                        "Estimated Savings": savings
                    })

            if savings_list:
                savings_df = pd.DataFrame(savings_list)
                st.write("Estimated Savings for This Service Type:")
                st.dataframe(savings_df)
                all_savings.append(savings_df)
            else:
                st.info(f"No overlapping contracts found for {service}.")

        #Final summary of all potential savings.
        if all_savings:
            final_df = pd.concat(all_savings, ignore_index=True)
            st.subheader("Total Estimated Savings Across All Service Types")
            st.dataframe(final_df)

            total_savings = final_df["Estimated Savings"].sum()
            st.metric("Total Estimated Savings", f"${total_savings:,.2f}")
        else:
            st.info("No overlapping contracts found in any selected Service Type.")
else:
    st.warning("Please upload an Excel file to get started.")

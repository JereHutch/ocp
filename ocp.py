"""
Jeremiah Hutchison
Program Name: ocproject.py
Description: A program to take an excel datasheet and give the savings potential
for contracts that overlap each other. We will be using streamlit, pandas, and plotly.express
for the framework and manipulation of the data. 
"""

#We'll be using Streamlit as the framework and Pandas for the dataframes.
import streamlit as st
import pandas as pd
import plotly.express as px

#Let's Show the TITLE and LOGO!
st.set_page_config(page_title="Contract Overlap Analyzer", layout="wide")
st.title("Overlapinator: Contract Overlap Analyzer")
st.write("Welcome! To Begin, Upload an Excel file with your contract data with the required columns.")
st.write("Required Columns: Contract_Name, Contract_ID, Service_Type, Start_Date, End_Date, Cost, Maintenance, Department")

#Upload their Excel File with their contract data.
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

#Define the function for grouping overlapping contracts.
def assign_overlap_groups(df, start_group_id=0):
    df = df.copy()
    df["Start_Date"] = pd.to_datetime(df["Start_Date"])
    df["End_Date"] = pd.to_datetime(df["End_Date"])
    df = df.sort_values("Start_Date").reset_index(drop=True)

    df["Overlap_Group"] = -1
    group_id = start_group_id
    current_end = pd.Timestamp.min

    for i, row in df.iterrows():
        start = row["Start_Date"]
        end = row["End_Date"]

        if start > current_end:
            current_end = end
            group_id += 1
        else:
            current_end = max(current_end, end)

        df.at[i, "Overlap_Group"] = group_id

    return df, group_id  #return the updated group_id

#Now we setup the main idea for the project itself. Overlapping by Service Type.
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    #Make sure they have the right columns.
    required_cols = ["Contract_Name", "Contract_ID", "Service_Type", "Start_Date", "End_Date", "Cost", "Maintenance", "Department"]
    if not all(col in df.columns for col in required_cols):
        st.error(f"Missing one or more required columns: {', '.join(required_cols)}")
    else:
        #Calculate the total cost of the contract.
        df["Total Cost"] = df["Cost"] + df["Maintenance"]

        #Sidebar Filters
        with st.sidebar:
            st.image("BongoLogo.PNG", width=120)
            st.markdown("### Filter Your Contracts")

            search_query = st.text_input("Search by Contract Name or ID🔎")

            service_types = df["Service_Type"].unique()
            selected_types = st.multiselect("Service Type", service_types, default=service_types)

            departments = df["Department"].dropna().unique()
            selected_departments = st.multiselect("Department", departments, default=departments)

        if search_query:
            df = df[
                df["Contract_Name"].str.contains(search_query, case=False, na=False) |
                df["Contract_ID"].astype(str).str.contains(search_query, case=False, na=False)
            ]

        df = df[df["Service_Type"].isin(selected_types)]
        df = df[df["Department"].isin(selected_departments)]

        all_grouped = []
        all_savings = []
        group_id_counter = 0

        #Process each Service Type separately in their own group.
        for service in selected_types:
            st.subheader(f"Service Type: {service}")
            df_service = df[df["Service_Type"] == service].copy()
            
            #Get grouped dataframe and update the group_id_counter
            df_grouped, group_id_counter = assign_overlap_groups(df_service, start_group_id=group_id_counter)
            all_grouped.append(df_grouped)

            st.write("Overlapping Contracts:")
            st.dataframe(df_grouped)

            #Calculate those savings.
            savings_list = []
            for group, group_df in df_grouped.groupby("Overlap_Group"):
                if len(group_df) > 1:
                    st.markdown(f"#### 🔀Overlap Group {group} - {service}")
                    selected_contracts = []
                    for _, row in group_df.iterrows():
                        contract_id = row["Contract_ID"]
                        label = f"{row['Contract_Name']} (Vendor: {contract_id}, Cost: ${row['Cost']}, Maintenance: ${row['Maintenance']})"
                        if st.checkbox(f"Keep: {label}", key=f"{service}_{group}_{contract_id}"):
                            selected_contracts.append(contract_id)

                    total_cost = group_df["Total Cost"].sum()
                    kept_df = group_df[group_df["Contract_ID"].isin(selected_contracts)]

                    if not kept_df.empty:
                        kept_cost = kept_df["Total Cost"].sum()
                        savings = total_cost - kept_cost

                        savings_list.append({
                            "Service_Type": service,
                            "Overlap_Group": group,
                            "Total Group Cost": total_cost,
                            "User Selected Contracts Cost": kept_cost,
                            "Estimated Savings": savings
                        })

            if savings_list:
                savings_df = pd.DataFrame(savings_list)
                st.write("Estimated Savings for This Service Type:")
                st.dataframe(savings_df)
                all_savings.append(savings_df)
            else:
                st.info(f"Assumption: No overlapping contracts found for {service}.")

        #Final summary of all potential savings.
        if all_savings:
            final_df = pd.concat(all_savings, ignore_index=True)
            st.subheader("Total Estimated Savings Across All Service Types")

            #Show what contracts where kept and total overlapping.
            total_overlapping = sum(len(g) for g in all_grouped if g["Overlap_Group"].nunique() > 1)
            retained_contract_ids = final_df["Selected Contracts Cost"].count()

            col1, col2 = st.column(2)
            col1.metric("Total Overlapping Contracts", total_overlapping)
            col2.metric("Contracts Selected to Keep", retained_contract_ids)

            #Let's show the last savings table
            st.dataframe(final_df, use_container_width=True)
            total_savings = final_df["Estimated Savings"].sum()
            st.metric("🔥Total Estimated Savings", f"${total_savings:,.2f}")

            #Optional Download
            st.download_button(
                label="Download Savings Report",
                data=final_df.to_csv(index=False),
                file_name="savings_report.csv",
                mime="text/csv"
            )

            #Let's now add a pie chart to show our data.
            pie_data = final_df.groupby("Service_Type")["Estimated Savings"].sum().reset_index()
            fig = px.pie(pie_data, names="Service_Type", values="Estimated Savings",
                         title="Savings by Service Type", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No overlapping contracts found in any selected Service Type.")
else:
    st.warning("Please upload an Excel file to get started.")



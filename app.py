
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Generator Planning Casieri", layout="centered")
st.title("🗓️ Generator de Planning pentru Casieri")

# Upload Excel file
uploaded_file = st.file_uploader("📁 Încarcă fișierul Excel cu condițiile echipei:", type=["xlsx"])

# Select month and year
col1, col2 = st.columns(2)
with col1:
    selected_month = st.selectbox("📅 Selectează luna:", list(range(1, 13)), format_func=lambda x: datetime(2025, x, 1).strftime('%B'))
with col2:
    selected_year = st.number_input("📆 Anul:", min_value=2024, max_value=2030, value=2025, step=1)

# Process file and generate schedule
if uploaded_file:
    try:
        df_conditions = pd.read_excel(uploaded_file)

        # Placeholder logic for planning (to be replaced by actual logic)
        num_days = (datetime(selected_year, selected_month % 12 + 1, 1) - timedelta(days=1)).day
        casieri = df_conditions['Nume']
        schedule = []

        for i in range(1, num_days + 1):
            date = datetime(selected_year, selected_month, i)
            for idx, casier in enumerate(casieri):
                shift = 'Dimineață' if idx % 2 == 0 else 'După-amiază'
                schedule.append({
                    'Data': date.strftime('%Y-%m-%d'),
                    'Casier': casier,
                    'Tura': shift
                })

        df_schedule = pd.DataFrame(schedule)
        st.success("✅ Planningul a fost generat cu succes!")
        st.dataframe(df_schedule)

        # Download Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_schedule.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            label="⬇️ Descarcă planningul în Excel",
            data=output,
            file_name=f"planning_casieri_{selected_month}_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Eroare la procesarea fișierului: {e}")
else:
    st.info("ℹ️ Încarcă un fișier Excel pentru a începe.")

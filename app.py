
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Generator Planning Casieri", layout="centered")
st.title("🗓️ Generator de Planning pentru Casieri")

uploaded_file = st.file_uploader("📁 Încarcă fișierul Excel cu condițiile echipei:", type=["xlsx"])

col1, col2 = st.columns(2)
with col1:
    selected_month = st.selectbox("📅 Selectează luna:", list(range(1, 13)), format_func=lambda x: datetime(2025, x, 1).strftime('%B'))
with col2:
    selected_year = st.number_input("📆 Anul:", min_value=2024, max_value=2030, value=2025, step=1)

if uploaded_file:
    try:
        df_conditions = pd.read_excel(uploaded_file)
        df_conditions.fillna("", inplace=True)
        df_conditions['Preferinta_1'] = pd.to_datetime(df_conditions['Preferinta_1'], errors='coerce')
        df_conditions['Preferinta_2'] = pd.to_datetime(df_conditions['Preferinta_2'], errors='coerce')
        df_conditions['Concediu_Start'] = pd.to_datetime(df_conditions['Concediu_Start'], errors='coerce')
        df_conditions['Concediu_Sfarsit'] = pd.to_datetime(df_conditions['Concediu_Sfarsit'], errors='coerce')

        first_day = datetime(selected_year, selected_month, 1)
        num_days = (datetime(selected_year, selected_month % 12 + 1, 1) - timedelta(days=1)).day

        casieri = df_conditions['Nume'].tolist()
        planning = []
        status = {
            nume: {
                "zile_lucrate": 0,
                "libere": [],
                "ultima_tura": df_conditions.loc[df_conditions['Nume'] == nume, 'Tura_Finala_Anterioara'].values[0],
                "weekenduri_libere": 0,
                "sapt_curenta": "Dimineață" if df_conditions.loc[df_conditions['Nume'] == nume, 'Tura_Finala_Anterioara'].values[0] == 'După-amiază' else "După-amiază",
                "zile_weekend": []
            } for nume in casieri
        }

        for zi in range(1, num_days + 1):
            data = datetime(selected_year, selected_month, zi)
            zi_sapt = data.strftime('%A')
            is_weekend = zi_sapt in ['Saturday', 'Sunday']
            zi_str = data.strftime('%Y-%m-%d')
            saptamana_index = (data - first_day).days // 7

            for nume in status:
                status[nume]['sapt_curenta'] = 'Dimineață' if saptamana_index % 2 == 0 else 'După-amiază'

            disponibili = []
            for _, row in df_conditions.iterrows():
                nume = row['Nume']
                if row['Concediu_Start'] and row['Concediu_Sfarsit'] and row['Concediu_Start'] <= data <= row['Concediu_Sfarsit']:
                    continue
                if data == row['Preferinta_1'] or data == row['Preferinta_2']:
                    continue
                if status[nume]['zile_lucrate'] >= 5:
                    status[nume]['zile_lucrate'] = 0
                    status[nume]['libere'].append(zi_str)
                    continue
                if is_weekend and status[nume]['weekenduri_libere'] >= 1.5:
                    continue
                disponibili.append(nume)

            if len(disponibili) < 16:
                st.warning(f"⚠️ Ziua {zi_str} are mai puțin de 16 casieri disponibili.")

            dim_slots = ["07:00"] * 4 + ["08:00"] * 2 + ["09:00"] * 2 if not is_weekend else ["07:00"] * 4 + ["08:00"] * 3 + ["09:00"] * 2
            dupa_slots = ["14:00"] * (7 if is_weekend else 8)
            dim_casieri = [c for c in disponibili if status[c]['sapt_curenta'] == 'Dimineață'][:len(dim_slots)]
            for idx, casier in enumerate(dim_casieri):
                planning.append({"Data": zi_str, "Casier": casier, "Tura": "Dimineață", "Ora_Start": dim_slots[idx]})
                status[casier]['zile_lucrate'] += 1
                status[casier]['ultima_tura'] = 'Dimineață'
                if is_weekend:
                    status[casier]['zile_weekend'].append(data)

            ramasi = [c for c in disponibili if c not in dim_casieri and status[c]['sapt_curenta'] == 'După-amiază']
            dupa_casieri = ramasi[:len(dupa_slots)]
            for idx, casier in enumerate(dupa_casieri):
                if status[casier]['ultima_tura'] == 'După-amiază' and zi > 1 and status[casier]['zile_lucrate'] > 0:
                    continue
                planning.append({"Data": zi_str, "Casier": casier, "Tura": "După-amiază", "Ora_Start": dupa_slots[idx]})
                status[casier]['zile_lucrate'] += 1
                status[casier]['ultima_tura'] = 'După-amiază'
                if is_weekend:
                    status[casier]['zile_weekend'].append(data)

            for nume in status:
                weekenduri = len(set(d.date() for d in status[nume]['zile_weekend'])) / 2
                status[nume]['weekenduri_libere'] = max(0, 3 - weekenduri)

        df_schedule = pd.DataFrame(planning)
        st.success("✅ Planningul complet a fost generat!")
        st.dataframe(df_schedule)

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

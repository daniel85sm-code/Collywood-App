import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- CONFIGURAZIONE ---
DATABASE_NAME = "collywood_hr_vault.csv"
WHITELIST_FILE = "autorizzati.csv"
ADMIN_EMAIL = "daniel85sm@gmail.com"

st.set_page_config(page_title="Collywood HR System", layout="wide")

# --- FUNZIONI DI SERVIZIO ---
def calcola_ore_totali(inizio_str, fine_str):
    fmt = "%H:%M"
    try:
        inizio = datetime.strptime(inizio_str.strip(), fmt)
        fine = datetime.strptime(fine_str.strip(), fmt)
        if fine < inizio:
            differenza = (fine + timedelta(days=1)) - inizio
        else:
            differenza = fine - inizio
        return round(differenza.total_seconds() / 3600, 2)
    except:
        return 0.0

def carica_whitelist():
    if os.path.exists(WHITELIST_FILE):
        return pd.read_csv(WHITELIST_FILE)['email'].tolist()
    return [ADMIN_EMAIL]

def salva_whitelist(lista_email):
    pd.DataFrame({'email': lista_email}).to_csv(WHITELIST_FILE, index=False)

# --- LOGIN ---
if "user_role" not in st.session_state:
    st.session_state.user_role = None

whitelist = carica_whitelist()

if not st.session_state.user_role:
    st.title("🔐 Collywood Auth Portal")
    email_input = st.text_input("Inserisci la tua Email").lower().strip()
    
    if st.button("Accedi"):
        if email_input in whitelist:
            if email_input == ADMIN_EMAIL:
                st.session_state.user_role = "Manager"
                st.session_state.user_name = "Daniel (Admin)"
            else:
                st.session_state.user_role = "Employee"
                st.session_state.user_name = email_input.split("@")[0].capitalize()
            st.rerun()
        else:
            st.error("⛔ Email non autorizzata.")
    st.stop()

# --- INTERFACCIA DIPENDENTE ---
if st.session_state.user_role == "Employee":
    st.title(f"👋 Ciao {st.session_state.user_name}")
    
    stato_turno = "chiuso"
    if os.path.exists(DATABASE_NAME):
        df_check = pd.read_csv(DATABASE_NAME)
        oggi = str(datetime.now().date())
        aperto = df_check[(df_check['Dipendente'] == st.session_state.user_name) & 
                          (df_check['Data'] == oggi) & (df_check['Fine'].isna())]
        if not aperto.empty:
            stato_turno = "aperto"

    if stato_turno == "chiuso":
        if st.button("🚀 INIZIA TURNO", use_container_width=True, type="primary"):
            ora_in = datetime.now().strftime("%H:%M")
            nuovo = pd.DataFrame([{"Data": str(datetime.now().date()), "Dipendente": st.session_state.user_name, "Inizio": ora_in, "Fine": None, "Ore": 0.0, "Motivazione": "Digitale"}])
            nuovo.to_csv(DATABASE_NAME, mode='a', header=not os.path.exists(DATABASE_NAME), index=False)
            st.success(f"Turno iniziato alle {ora_in}")
            st.rerun()
    else:
        if st.button("🏁 FINE TURNO", use_container_width=True):
            df = pd.read_csv(DATABASE_NAME)
            ora_out = datetime.now().strftime("%H:%M")
            idx = df[(df['Dipendente'] == st.session_state.user_name) & (df['Fine'].isna())].index[-1]
            ora_in = df.at[idx, 'Inizio']
            df.at[idx, 'Fine'] = ora_out
            df.at[idx, 'Ore'] = calcola_ore_totali(ora_in, ora_out)
            df.to_csv(DATABASE_NAME, index=False)
            st.success(f"Turno finito alle {ora_out}")
            st.rerun()

# --- INTERFACCIA MANAGER ---
else:
    st.title("👨‍💼 Manager Dashboard")
    tab1, tab2, tab3 = st.tabs(["Monitor", "Storico", "Staff"])
    with tab1:
        st.write("Qui vedi chi sta lavorando ora.")
    with tab2:
        if os.path.exists(DATABASE_NAME):
            st.dataframe(pd.read_csv(DATABASE_NAME))
    with tab3:
        # Qui puoi aggiungere le email dei dipendenti
        nuova = st.text_input("Aggiungi email dipendente")
        if st.button("Salva"):
            whitelist.append(nuova)
            salva_whitelist(whitelist)
            st.success("Aggiunto!")

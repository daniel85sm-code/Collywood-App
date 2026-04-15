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
        # Pulizia stringhe da eventuali spazi
        inizio_str = str(inizio_str).strip()
        fine_str = str(fine_str).strip()
        
        inizio = datetime.strptime(inizio_str, fmt)
        fine = datetime.strptime(fine_str, fmt)
        
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
            nuovo = pd.DataFrame([{"Data": str(datetime.now().date()), "Dipendente": st.session_state.user_name, "Inizio": ora_in, "Fine": None, "Ore": 0.0, "Motivazione": "Timbratura Digitale"}])
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
    
    if st.button("Log-out"):
        st.session_state.user_role = None
        st.rerun()

# --- INTERFACCIA MANAGER ---
else:
    st.title("👨‍💼 Manager Dashboard")
    tab1, tab2, tab3 = st.tabs(["📊 Storico & Modifica", "➕ Inserimento Manuale", "👥 Gestione Staff"])
    
    with tab1:
        st.subheader("Modifica o Elimina Turni")
        if os.path.exists(DATABASE_NAME):
            df = pd.read_csv(DATABASE_NAME)
            # Editor interattivo
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
            
            if st.button("💾 Salva e Ricalcola Ore"):
                # Ricalcola le ore per ogni riga prima di salvare
                for index, row in edited_df.iterrows():
                    if pd.notnull(row['Inizio']) and pd.notnull(row['Fine']):
                        edited_df.at[index, 'Ore'] = calcola_ore_totali(row['Inizio'], row['Fine'])
                
                edited_df.to_csv(DATABASE_NAME, index=False)
                st.success("Dati ricalcolati e salvati correttamente!")
                st.rerun()
        else:
            st.info("Ancora nessun dato registrato.")

    with tab2:
        st.subheader("Aggiungi Turno a Mano")
        with st.form("manual_form"):
            f_nome = st.text_input("Nome Dipendente")
            f_data = st.date_input("Data")
            f_in = st.time_input("Ora Inizio")
            f_out = st.time_input("Ora Fine")
            f_mot = st.text_area("Motivazione inserimento manuale")
            if st.form_submit_button("Registra Turno"):
                ora_i = f_in.strftime("%H:%M")
                ora_f = f_out.strftime("%H:%M")
                ore = calcola_ore_totali(ora_i, ora_f)
                nuovo = pd.DataFrame([{"Data": str(f_data), "Dipendente": f_nome, "Inizio": ora_i, "Fine": ora_f, "Ore": ore, "Motivazione": f_mot}])
                nuovo.to_csv(DATABASE_NAME, mode='a', header=not os.path.exists(DATABASE_NAME), index=False)
                st.success("Turno aggiunto correttamente!")
                st.rerun()

    with tab3:
        st.subheader("Autorizzazioni Accesso")
        nuova_mail = st.text_input("Email nuovo dipendente").lower().strip()
        if st.button("Aggiungi alla lista"):
            if nuova_mail and "@" in nuova_mail:
                if nuova_mail not in whitelist:
                    whitelist.append(nuova_mail)
                    salva_whitelist(whitelist)
                    st.success(f"{nuova_mail} aggiunto!")
                    st.rerun()
        
        st.write("---")
        for e in whitelist:
            if e != ADMIN_EMAIL:
                col1, col2 = st.columns([3, 1])
                col1.text(e)
                if col2.button("Elimina", key=e):
                    whitelist.remove(e)
                    salva_whitelist(whitelist)
                    st.rerun()

    if st.sidebar.button("Esci dal sistema"):
        st.session_state.user_role = None
        st.rerun()

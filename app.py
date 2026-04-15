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

# --- 2. LOGIN CON WHITELIST DINAMICA ---
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
            st.error("⛔ Email non autorizzata. Chiedi a Daniel di aggiungerti.")
    st.stop()

# --- 3. DASHBOARD ---

if st.session_state.user_role == "Employee":
    st.title(f"👋 Ciao {st.session_state.user_name}")
    st.info("Qui presto potrai timbrare con un click.")
    if st.button("Esci"):
        st.session_state.user_role = None
        st.rerun()

else:
    st.title("👨‍💼 Manager Dashboard")
    # Aggiungiamo un quarto Tab per la gestione utenti
    tab1, tab2, tab3, tab4 = st.tabs(["Monitor", "Storico", "Override", "👥 Gestione Staff"])
    
    with tab1:
        st.subheader("📡 Chi sta lavorando?")
        st.write("Funzione in arrivo...")

    with tab2:
        st.subheader("📂 Modifica Turni")
        if os.path.exists(DATABASE_NAME):
            df = pd.read_csv(DATABASE_NAME)
            # Editor interattivo
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
            if st.button("💾 Salva Modifiche Turni"):
                edited_df.to_csv(DATABASE_NAME, index=False)
                st.success("Dati aggiornati!")
        else:
            st.info("Nessun turno registrato.")

    with tab3:
        st.subheader("⚠️ Inserimento Manuale")
        with st.form("manual"):
            d_nome = st.text_input("Nome Dipendente")
            d_data = st.date_input("Data")
            d_in = st.time_input("Inizio")
            d_out = st.time_input("Fine")
            d_mot = st.text_area("Motivazione")
            if st.form_submit_button("Registra"):
                ore = calcola_ore_totali(d_in.strftime("%H:%M"), d_out.strftime("%H:%M"))
                nuovo = pd.DataFrame([{"Data": str(d_data), "Dipendente": d_nome, "Inizio": d_in.strftime("%H:%M"), "Fine": d_out.strftime("%H:%M"), "Ore": ore, "Motivazione": d_mot}])
                nuovo.to_csv(DATABASE_NAME, mode='a', header=not os.path.exists(DATABASE_NAME), index=False)
                st.success("Turno salvato!")

    with tab4:
        st.subheader("👥 Autorizza Nuovi Dipendenti")
        
        # 1. Aggiunta nuova email
        nuova_email = st.text_input("Inserisci l'email del nuovo dipendente:").lower().strip()
        if st.button("➕ Aggiungi alla Whitelist"):
            if nuova_email and "@" in nuova_email:
                if nuova_email not in whitelist:
                    whitelist.append(nuova_email)
                    salva_whitelist(whitelist)
                    st.success(f"L'email {nuova_email} ora può accedere all'app!")
                    st.rerun()
                else:
                    st.warning("Questa email è già autorizzata.")
            else:
                st.error("Inserisci un'email valida.")

        st.write("---")
        
        # 2. Visualizzazione e Rimozione
        st.write("✉️ **Email attualmente autorizzate:**")
        for e in whitelist:
            col_e, col_btn = st.columns([3, 1])
            col_e.text(e)
            if e != ADMIN_EMAIL: # Non permetterti di auto-cancellarti!
                if col_btn.button("Elimina", key=e):
                    whitelist.remove(e)
                    salva_whitelist(whitelist)
                    st.rerun()

    if st.sidebar.button("Log-out"):
        st.session_state.user_role = None
        st.rerun()
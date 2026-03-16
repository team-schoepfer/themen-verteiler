import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment

# --- KONFIGURATION ---
st.set_page_config(page_title="Themen-Verteiler", page_icon="🎯", layout="centered")

# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #9EB3C2;
    }}
    
    .stTabs, .stExpander, div[data-testid="stMetricValue"] {{
        background-color: rgba(255, 255, 255, 0.85);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }}

    .stButton>button {{
        border-radius: 20px;
        background-color: #1C2541;
        color: white;
        border: none;
        height: 3em;
        width: 100%;
    }}
    
    h1, h2, h3 {{
        color: #1C2541;
        text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- PASSWORT ---
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h1>🔐 Login</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            pwd = st.text_input("Passwort", type="password")
            if st.button("Anmelden"):
                if pwd == st.secrets["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Passwort leider falsch.")
        return False
    return True

if check_password():

    st.markdown("<h1>Themen-Verteiler</h1>", unsafe_allow_html=True)

     # --- ANLEITUNG ---
    with st.expander("Kurzanleitung: So funktioniert's", expanded=True):
        st.markdown("""
        1. **Excel vorbereiten:** Erstelle eine Liste mit den Spalten **Person**, **Prio 1**, **Prio 2** und **Prio 3**. (wenn ein Student keine Prioritäten angegeben hat, gib der Person trotzdem einen Namen, aber lass die anderen 3 Spalten frei)
        2. **Datei hochladen:** Ziehe die Datei in das Feld unten im Tab 'Datei-Upload'.
        3. **Themenangabe:** Gib an, wie viele Themen es insgesamt gibt.
        4. **Optimieren:** Wechsel zum Tab 'Ergebnis' und starte die Berechnung.
        5. **Download:** Speicher die fertige Zuweisung als CSV-Datei ab.
        """)

    tab1, tab2 = st.tabs(["Datei-Upload", "Ergebnis"])

    with tab1:

        uploaded_file = st.file_uploader("Excel-Datei hochladen (.xlsx)", type=["xlsx"])

        anzahl_themen = st.number_input(
          "Wie viele Themen gibt es insgesamt?",
          min_value=1,
          step=1
        )

        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.success(f"✅ Liste mit {len(df)} Personen geladen.")
                with st.expander("Vorschau"):
                    st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"Fehler beim Lesen der Datei: {e}")

    with tab2:

        if not uploaded_file:
            st.warning("⚠️ Bitte zuerst eine Datei hochladen.")
        else:

            if st.button("Optimale Verteilung berechnen"):

                # --- Themen sind einfach 1 bis N ---
                alle_themen = list(range(1, int(anzahl_themen) + 1))

                # Falls mehr Studierende als Themen → Dummy-Themen ergänzen
                if len(df) > len(alle_themen):
                    start = len(alle_themen) + 1
                    for i in range(len(df) - len(alle_themen)):
                        alle_themen.append(start + i)

                # --- Kostenmatrix ---
                kosten = np.full((len(df), len(alle_themen)), 100)
                thema_zu_idx = {thema: i for i, thema in enumerate(alle_themen)}

                for i, row in df.iterrows():

                    for prio, gewicht in zip(["Prio 1", "Prio 2", "Prio 3"], [1, 5, 15]):

                        if pd.notna(row[prio]):
                            try:
                                thema = int(row[prio])
                                if thema in thema_zu_idx:
                                    kosten[i, thema_zu_idx[thema]] = gewicht
                            except:
                                pass

                # --- Optimierung ---
                row_ind, col_ind = linear_sum_assignment(kosten)

                ergebnisse = []
                stats = {"Prio 1": 0, "Prio 2": 0, "Prio 3": 0, "Andere": 0}

                for r, c in zip(row_ind, col_ind):

                    prio_score = kosten[r, c]
                    prio_label = {
                        1: "Prio 1",
                        5: "Prio 2",
                        15: "Prio 3"
                    }.get(prio_score, "Andere")

                    stats[prio_label] += 1

                    ergebnisse.append({
                        "Person": df.iloc[r]["Person"],
                        "Thema": int(alle_themen[c]),   # <- garantiert ganze Zahl
                        "Ergebnis": prio_label
                    })

                res_df = pd.DataFrame(ergebnisse)

                # --- Statistik ---
                st.markdown("#### Zufriedenheits-Übersicht")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Prio 1", stats["Prio 1"])
                m2.metric("Prio 2", stats["Prio 2"])
                m3.metric("Prio 3", stats["Prio 3"])
                m4.metric("Andere", stats["Andere"])

                st.markdown("---")
                st.dataframe(res_df, use_container_width=True)

                # --- Download ---
                csv = res_df.to_csv(index=False).encode("utf-8-sig")

                st.download_button(
                    label="💾 Ergebnisse herunterladen (CSV)",
                    data=csv,
                    file_name="themenzuweisung.csv",
                    mime="text/csv"
                )

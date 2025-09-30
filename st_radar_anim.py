import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import io
import tempfile
import os
from matplotlib.animation import PillowWriter

st.set_page_config(page_title="Comparaison d'ETP entre un pays et un groupe ayant des niveaux de dépenses équivalents",
                   layout='wide')

# --- Données ---
df = pd.read_excel('socle_rh_24.xlsx', sheet_name='Feuil1')

# Nettoyage
df = df[df['Cat Stat'] != "G0"]
df = df[['région', 'Pays', 'Correspondance', 'ETP']]
df.dropna(inplace=True)

pivot_df = df.pivot_table(index=['région', 'Pays'],
                          columns='Correspondance',
                          values='ETP',
                          aggfunc='sum',
                          fill_value=0).reset_index()
pivot_df.columns.name = None

dfc = pd.read_excel('cred_radar.xlsx')
dfc.fillna(0, inplace=True)

# --- Widgets ---
regions = pivot_df["région"].unique()
région_filtrée = st.sidebar.selectbox("Sélectionnez une Region:", regions)
pays_région_filtrée = pivot_df[pivot_df["région"] == région_filtrée]["Pays"].unique()
co = st.sidebar.selectbox("Sélectionnez un pays", pays_région_filtrée)

listp = ["HT2_P105", "PDGM"]
prog = st.sidebar.selectbox("Sélectionner la nature de la dépense (P105 ou DGM):", listp)

# --- Animation radar ---
taille = [1.2, 2, 2.5, 3, 3.5, 5, 5.5, 7, 7.5, 8, 9, 10]

fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

def update(frame):
    ax.clear()
    i = taille[frame]

    val = dfc.loc[dfc["Pays"].str.lower() == co.lower(), prog].iloc[0]
    d = val / i

    df_filtre = dfc[(dfc[prog] >= val - d) & (dfc[prog] <= val + d)]
    categories_filtre = df_filtre["Pays"].unique()
    pivot_df2 = pivot_df[pivot_df['Pays'].isin(categories_filtre)]

    moyenne_iso = pivot_df2[["Chancellerie", "Consulaire", "DCSD", "EAF/AF/EXT", "SCAC", "Support"]].mean().to_frame().T
    moyenne_iso.insert(0, 'Pays', "moyenne iso 105")
    moyenne_iso.insert(0, 'région', "iso 105")

    df_extended = pd.concat([pivot_df, moyenne_iso], ignore_index=True)
    df_subset = df_extended[df_extended["Pays"].isin([co, "moyenne iso 105"])]

    categories_radar = ["Chancellerie", "Consulaire", "DCSD", "EAF/AF/EXT", "SCAC", "Support"]
    N = len(categories_radar)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    for _, row in df_subset.iterrows():
        values = row[categories_radar].tolist()
        values += values[:1]
        ax.plot(angles, values, linewidth=2, label=row["Pays"])
        ax.fill(angles, values, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories_radar)
    ax.set_title(f"Radar comparant les ETP ({prog}) – tolérance taille = {i}", y=1.1)
    ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))

ani = animation.FuncAnimation(fig, update, frames=len(taille), interval=2000, repeat=True)

# Sauvegarde en GIF pour Streamlit
#buf = io.BytesIO()
#ani.save(buf, format="gif")
#st.image(buf.getvalue())

# interval défini dans FuncAnimation (en ms)
interval = 2000  # si vous avez utilisé interval=2000 plus haut
fps = 1000 / interval  # fps correspondant à l'interval (ex: 2000 ms -> 0.5 fps)

tmpname = None
try:
    # crée un fichier temporaire .gif
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
        tmpname = tmp.name

    # sauvegarde l'animation dans le fichier temporaire avec PillowWriter
    ani.save(tmpname, writer=PillowWriter(fps=fps))

    # lit le GIF et l'affiche dans Streamlit
    with open(tmpname, "rb") as f:
        gif_bytes = f.read()
    st.image(gif_bytes)

finally:
    # supprime le fichier temporaire
    if tmpname and os.path.exists(tmpname):
        os.remove(tmpname)

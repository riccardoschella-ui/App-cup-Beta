import streamlit as st
import cv2
import numpy as np
import easyocr
import math

def applica_arrotondamento(area_reale):
    """Applica le regole di arrotondamento del manuale Creset."""
    if area_reale < 0.03: # Sotto i 300cmq non si censice
        return 0, "Esente ( < 300cmq )"
    if area_reale <= 1.0:
        return 1.0, "Arrotondato a 1mq"
    else:
        # Arrotondamento al mezzo metro quadrato superiore
        return math.ceil(area_reale * 2) / 2, "Arrotondato a 0.5mq"

def analizza_cartellone_v2(image_array, distanza):
    # Parametri tecnici S25 Plus
    FOCALE_PIXEL = 3200 
    
    # Inizializza OCR
    reader = easyocr.Reader(['it'])
    results = reader.readtext(image_array)
    
    if not results:
        return None

    # Trova il messaggio con l'area del bounding box più grande
    # Ogni result è: (coordinate, testo, confidenza)
    messaggio_principale = max(results, key=lambda x: (x[0][2][0]-x[0][0][0]) * (x[0][2][1]-x[0][0][1]))
    
    # Calcolo dimensioni basato sul box del testo più grande
    box = messaggio_principale[0]
    width_px = abs(box[1][0] - box[0][0])
    height_px = abs(box[2][1] - box[1][1])
    
    larghezza_m = (width_px * distanza) / FOCALE_PIXEL
    altezza_m = (height_px * distanza) / FOCALE_PIXEL
    area_reale = larghezza_m * altezza_m
    
    area_fiscale, nota_fiscale = applica_arrotondamento(area_reale)
    
    return {
        "messaggio": messaggio_principale[1],
        "area_reale": round(area_reale, 3),
        "area_fiscale": area_fiscale,
        "nota": nota_fiscale,
        "esenzione_insegna": "Sì" if area_reale <= 5.0 else "No (Oltre 5mq)" #
    }

# --- Interfaccia Streamlit ---
st.title("📏 Censore Professionale ICP")
dist = st.number_input("Distanza misurata (metri)", 0.5, 50.0, 5.0)
file = st.file_uploader("Foto Mezzo Pubblicitario")

if file:
    img = np.array(Image.open(file))
    res = analizza_cartellone_v2(img, dist)
    
    if res:
        st.subheader(f"Messaggio rilevato: {res['messaggio']}")
        col1, col2 = st.columns(2)
        col1.metric("Superficie Reale", f"{res['area_reale']} m²")
        col2.metric("Superficie Imponibile", f"{res['area_fiscale']} m²")
        st.info(f"Nota normativa: {res['nota']}")
        
        if res['esenzione_insegna'] == "Sì":
            st.warning("Potenziale Esenzione: Insegna d'esercizio ≤ 5 m²")


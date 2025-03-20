import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from folium.plugins import Draw, LocateControl, MeasureControl, Fullscreen
import numpy as np
import time
import altair as alt
import json
from branca.colormap import linear

# O'simlik turlari va ularning xususiyatlari
osimlik_turlari = {
    "bug'doy": {
        "sugorish_davri": 10,  # Kunlarda
        "pishib_yetilish_muddat": 4,  # Oylarda
        "namlik_minimum": 30,
        "namlik_optimal": 60,
        "qurish_tezligi": 1.5
    },
    "makkajo'xori": {
        "sugorish_davri": 7,
        "pishib_yetilish_muddat": 3,
        "namlik_minimum": 40,
        "namlik_optimal": 70,
        "qurish_tezligi": 2.0
    },
    "sholi": {
        "sugorish_davri": 4,
        "pishib_yetilish_muddat": 4,
        "namlik_minimum": 60,
        "namlik_optimal": 90,
        "qurish_tezligi": 2.5
    },
    "paxta": {
        "sugorish_davri": 8,
        "pishib_yetilish_muddat": 5,
        "namlik_minimum": 35,
        "namlik_optimal": 65,
        "qurish_tezligi": 1.8
    },
    "sabzavotlar": {
        "sugorish_davri": 4,
        "pishib_yetilish_muddat": 2,
        "namlik_minimum": 45,
        "namlik_optimal": 75,
        "qurish_tezligi": 2.2
    },
    "kartoshka": {
        "sugorish_davri": 6,
        "pishib_yetilish_muddat": 3,
        "namlik_minimum": 40,
        "namlik_optimal": 70,
        "qurish_tezligi": 1.7
    },
    "beda": {
        "sugorish_davri": 12,
        "pishib_yetilish_muddat": 2,
        "namlik_minimum": 35,
        "namlik_optimal": 65,
        "qurish_tezligi": 1.4
    },
    "pomidor": {
        "sugorish_davri": 3,
        "pishib_yetilish_muddat": 3,
        "namlik_minimum": 50,
        "namlik_optimal": 80,
        "qurish_tezligi": 2.3
    },
    "bodring": {
        "sugorish_davri": 2,
        "pishib_yetilish_muddat": 2,
        "namlik_minimum": 55,
        "namlik_optimal": 85,
        "qurish_tezligi": 2.4
    }
}


# Maydon rangini sug'orish jadvali va tuproq namligiga qarab aniqlash funksiyasi
def maydon_rangini_olish(oxirgi_sugorilgan, ekin_turi, tuproq_namligi, ekish_sanasi=None):
    if ekin_turi not in osimlik_turlari:
        return "gray", "Ekin turi tanlanmagan"

    sugorish_davri = osimlik_turlari[ekin_turi]["sugorish_davri"]
    namlik_minimum = osimlik_turlari[ekin_turi]["namlik_minimum"]
    namlik_optimal = osimlik_turlari[ekin_turi]["namlik_optimal"]

    sugorishdan_otgan_kunlar = (datetime.date.today() - oxirgi_sugorilgan).days

    # Pishib yetilish muddatini hisoblash
    pishib_yetilish_holati = ""
    if ekish_sanasi:
        pishib_yetilish_muddat = osimlik_turlari[ekin_turi]["pishib_yetilish_muddat"] * 30  # oy kunlarga
        utgan_kunlar = (datetime.date.today() - ekish_sanasi).days
        qolgan_kunlar = pishib_yetilish_muddat - utgan_kunlar

        if qolgan_kunlar <= 0:
            pishib_yetilish_holati = "Pishib yetilgan"
        else:
            pishib_yetilish_holati = f"Pishib yetilishga {qolgan_kunlar} kun qoldi"

    # Namlik holatini baholash
    if tuproq_namligi < namlik_minimum and sugorishdan_otgan_kunlar >= sugorish_davri:
        return "red", f"Tezda sug'orish kerak. {pishib_yetilish_holati}"
    elif tuproq_namligi < namlik_minimum * 1.2 and sugorishdan_otgan_kunlar >= sugorish_davri - 2:
        return "orange", f"Sug'orish kuni yaqinlashmoqda. {pishib_yetilish_holati}"
    elif tuproq_namligi > namlik_optimal * 0.8 and sugorishdan_otgan_kunlar < sugorish_davri:
        return "green", f"Yaqinda sug'orilgan. {pishib_yetilish_holati}"
    elif pishib_yetilish_holati == "Pishib yetilgan":
        return "purple", "Ekin hosilga tayyor"
    else:
        return "blue", f"Normal holat. {pishib_yetilish_holati}"


# Sessiya holatini ishga tushirish
def initialize_session_state():
    if 'maydonlar' not in st.session_state:
        st.session_state.maydonlar = []
    if 'oxirgi_yangilanish' not in st.session_state:
        st.session_state.oxirgi_yangilanish = time.time()
    if 'tanlangan_maydon' not in st.session_state:
        st.session_state.tanlangan_maydon = None
    if 'xarita_markazi' not in st.session_state:
        st.session_state.xarita_markazi = [41.3775, 64.5853]  # O'zbekiston markazi
    if 'xarita_zoom' not in st.session_state:
        st.session_state.xarita_zoom = 6
    if 'demo_yaratildi' not in st.session_state:
        st.session_state.demo_yaratildi = False


# Demo maydonlarni yaratish funksiyasi
def demo_maydonlar_yaratish():
    if not st.session_state.demo_yaratildi:
        bugun = datetime.date.today()
        demo_maydonlar = [
            {
                "nomi": "Paxta maydoni 1", "ekin": "paxta",
                "oxirgi_sugorilgan": bugun - datetime.timedelta(days=7),
                "ekish_sanasi": bugun - datetime.timedelta(days=60),
                "tuproq_namligi": 35,
                "shakl": {
                    "type": "Feature", "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[64.6, 41.38], [64.62, 41.38], [64.62, 41.39], [64.6, 41.39], [64.6, 41.38]]]
                    }
                }
            },
            {
                "nomi": "Bug'doy maydoni", "ekin": "bug'doy",
                "oxirgi_sugorilgan": bugun - datetime.timedelta(days=9),
                "ekish_sanasi": bugun - datetime.timedelta(days=90),
                "tuproq_namligi": 25,
                "shakl": {
                    "type": "Feature", "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[64.63, 41.38], [64.65, 41.38], [64.65, 41.39], [64.63, 41.39], [64.63, 41.38]]]
                    }
                }
            },
            {
                "nomi": "Pomidor maydoni", "ekin": "pomidor",
                "oxirgi_sugorilgan": bugun - datetime.timedelta(days=2),
                "ekish_sanasi": bugun - datetime.timedelta(days=80),
                "tuproq_namligi": 55,
                "shakl": {
                    "type": "Feature", "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[64.61, 41.4], [64.63, 41.4], [64.63, 41.41], [64.61, 41.41], [64.61, 41.4]]]
                    }
                }
            }
        ]
        st.session_state.maydonlar.extend(demo_maydonlar)
        st.session_state.demo_yaratildi = True
        st.session_state.xarita_markazi = [41.39, 64.625]
        st.session_state.xarita_zoom = 12


# Tuproq namligini simulyatsiya qilish funksiyasi
def tuproq_namligini_yangilash():
    hozir = time.time()
    if hozir - st.session_state.oxirgi_yangilanish > 5:  # Har 5 sekundda yangilash
        for i, maydon in enumerate(st.session_state.maydonlar):
            # Oxirgi sug'orishdan o'tgan vaqtga asosan namlikni kamaytirish
            sugorishdan_otgan_kunlar = (datetime.date.today() - maydon["oxirgi_sugorilgan"]).days

            # Ekin turiga qarab qurishni simulyatsiya qilish
            if maydon["ekin"] in osimlik_turlari:
                qurish_koeffitsienti = osimlik_turlari[maydon["ekin"]]["qurish_tezligi"]
            else:
                qurish_koeffitsienti = 1.5

            # Tasodifiy o'zgarish (-0.5 dan 0.5 gacha)
            tasodifiy_ozgarish = np.random.uniform(-0.5, 0.5)

            # Namlik kamayishini hisoblash
            namlik_kamayishi = (qurish_koeffitsienti * sugorishdan_otgan_kunlar / 10) + tasodifiy_ozgarish

            # Namlik qiymatini yangilash (0 dan kam bo'lmasligi kerak)
            yangi_namlik = max(0, maydon["tuproq_namligi"] - namlik_kamayishi)
            st.session_state.maydonlar[i]["tuproq_namligi"] = yangi_namlik

        st.session_state.oxirgi_yangilanish = hozir


# Maydonni tanlash funksiyasi
def maydonni_tanlash(indeks):
    st.session_state.tanlangan_maydon = indeks


# Maydonni sug'orish funksiyasi
def maydonni_sugorish():
    if st.session_state.tanlangan_maydon is not None:
        idx = st.session_state.tanlangan_maydon
        st.session_state.maydonlar[idx]["oxirgi_sugorilgan"] = datetime.date.today()

        if st.session_state.maydonlar[idx]["ekin"] in osimlik_turlari:
            optimal_namlik = osimlik_turlari[st.session_state.maydonlar[idx]["ekin"]]["namlik_optimal"]
            st.session_state.maydonlar[idx]["tuproq_namligi"] = optimal_namlik
        else:
            st.session_state.maydonlar[idx]["tuproq_namligi"] = 80

        st.success(f"{st.session_state.maydonlar[idx]['nomi']} muvaffaqiyatli sug'orildi!")


# Asosiy sahifa ko'rsatish funksiyasi
def show_xarita_page():
    # Sessiya holatini ishga tushirish
    initialize_session_state()

    # Yangilash funksiyasini chaqirish
    tuproq_namligini_yangilash()

    # Zonani ko'rsatish
    st.header("Aqlli Sug'orish Tizimi")
    st.caption("Dehqon xo'jaligi o'simliklari yetishtirish va sug'orish boshqaruvi")

    # Asosiy ko'rsatkichlar
    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
    with metrics_col1:
        st.metric("Jami maydonlar", f"{len(st.session_state.maydonlar)} ta")
    with metrics_col2:
        # Sug'orish talab qilinadigan maydonlar sonini hisoblash
        urgent_fields = 0
        for maydon in st.session_state.maydonlar:
            if maydon["ekin"] in osimlik_turlari:
                sugorish_davri = osimlik_turlari[maydon["ekin"]]["sugorish_davri"]
                sugorishdan_otgan_kunlar = (datetime.date.today() - maydon["oxirgi_sugorilgan"]).days
                if sugorishdan_otgan_kunlar >= sugorish_davri:
                    urgent_fields += 1
        st.metric("Sug'orish talab qilinadigan", f"{urgent_fields} ta")
    with metrics_col3:
        st.metric("Suv sarfi (bugun)", "120 L")
    with metrics_col4:
        st.metric("Suv sarfi (haftalik)", "840 L")

    # Ekin turlari haqida ma'lumot
    with st.expander("🌱 Ekin turlari va ularning sug'orish davriyligini ko'rish"):
        ekin_data = []
        for ekin, info in osimlik_turlari.items():
            ekin_data.append({
                "Ekin nomi": ekin,
                "Sug'orish davri (kun)": info["sugorish_davri"],
                "Pishib yetilish muddati (oy)": info["pishib_yetilish_muddat"],
                "Minimal namlik": f"{info['namlik_minimum']}%",
                "Optimal namlik": f"{info['namlik_optimal']}%"
            })

        st.table(pd.DataFrame(ekin_data))

    # Umumiy ma'lumotlar sarlavhasi
    st.header("Maydonlarni boshqarish")

    # Ustunlar yaratish
    chap_ustun, ong_ustun = st.columns([2, 1])

    # Chap ustun - Xarita
    with chap_ustun:
        st.subheader("Joylashuv xaritasi")

        # Demo maydonlar tugmasi
        if not st.session_state.demo_yaratildi:
            if st.button("📊 Demo maydonlarni yaratish"):
                demo_maydonlar_yaratish()

        # Xarita yaratish
        xarita_obyekti = folium.Map(location=st.session_state.xarita_markazi, zoom_start=st.session_state.xarita_zoom,
                                    tiles="CartoDB dark_matter", control_scale=True)

        # Xarita boshqaruvlarini qo'shish
        chizish_opsiyalari = {
            'polyline': True,
            'polygon': True,
            'rectangle': True,
            'circle': True,
            'marker': True,
            'circlemarker': True
        }

        tahrirlash_opsiyalari = {
            'edit': True,
            'remove': True,
            'poly': {
                'allowIntersection': False
            },
            'featureGroup': None,
            'rotateFlag': True
        }

        Draw(export=True,
             draw_options=chizish_opsiyalari,
             edit_options=tahrirlash_opsiyalari).add_to(xarita_obyekti)

        LocateControl(auto_start=False, position='topleft').add_to(xarita_obyekti)
        MeasureControl(position='topleft', primary_length_unit='kilometers').add_to(xarita_obyekti)
        Fullscreen(position='topleft').add_to(xarita_obyekti)

        # Xarita qatlamlarini qo'shish
        folium.TileLayer("Esri WorldImagery", attr="Esri").add_to(xarita_obyekti)
        folium.TileLayer("CartoDB positron", attr="© OpenStreetMap contributors").add_to(xarita_obyekti)
        folium.TileLayer("OpenStreetMap", attr="© OpenStreetMap contributors").add_to(xarita_obyekti)
        folium.LayerControl().add_to(xarita_obyekti)

        # Rang va holatlar uchun legend
        legend_html = '''
        <div style="position: fixed; bottom: 50px; right: 50px; z-index:1000; background-color: white; padding: 10px; border: 1px solid grey; border-radius: 5px;">
        <p><strong>Maydon holati:</strong></p>
        <p><span style="color:red;">■</span> Tezda sug'orish kerak</p>
        <p><span style="color:orange;">■</span> Sug'orish kuni yaqin</p>
        <p><span style="color:green;">■</span> Yaqinda sug'orilgan</p>
        <p><span style="color:blue;">■</span> Normal holat</p>
        <p><span style="color:purple;">■</span> Hosilga tayyor</p>
        </div>
        '''
        xarita_obyekti.get_root().html.add_child(folium.Element(legend_html))

        # Mavjud maydonlarni xaritaga qo'shish
        for i, maydon in enumerate(st.session_state.maydonlar):
            if "shakl" in maydon and maydon["shakl"]:
                ekish_sanasi = maydon.get("ekish_sanasi", None)
                rang, holat = maydon_rangini_olish(maydon["oxirgi_sugorilgan"], maydon["ekin"],
                                                   maydon["tuproq_namligi"],
                                                   ekish_sanasi)

                # GeoJSON obyektini yaratish
                if "geometry" in maydon["shakl"]:
                    geo_json = maydon["shakl"]
                else:
                    geo_json = {
                        "type": "Feature",
                        "geometry": maydon["shakl"]
                    }

                # Sug'orish davrini olish
                if maydon["ekin"] in osimlik_turlari:
                    sugorish_davri = osimlik_turlari[maydon["ekin"]]["sugorish_davri"]
                    pishib_yetilish_muddat = osimlik_turlari[maydon["ekin"]]["pishib_yetilish_muddat"]
                else:
                    sugorish_davri = "Aniqlanmagan"
                    pishib_yetilish_muddat = "Aniqlanmagan"

                # Pishib yetilish muddatini hisoblash
                if ekish_sanasi:
                    pishib_yetilish_kuni = ekish_sanasi + datetime.timedelta(days=pishib_yetilish_muddat * 30)
                    qolgan_kunlar = (pishib_yetilish_kuni - datetime.date.today()).days
                    if qolgan_kunlar > 0:
                        pishib_yetilish_holati = f"Pishib yetilishga {qolgan_kunlar} kun qoldi"
                    else:
                        pishib_yetilish_holati = "Pishib yetilgan"
                else:
                    pishib_yetilish_holati = "Ekish sanasi kiritilmagan"

                # Popup ma'lumotini yaratish
                popup = folium.Popup(
                    f"<b>{maydon['nomi']}</b><br>" +
                    f"Ekin: {maydon['ekin']}<br>" +
                    f"Sug'orish davri: {sugorish_davri} kun<br>" +
                    f"Pishib yetilish: {pishib_yetilish_muddat} oy<br>" +
                    f"Oxirgi sug'orilgan: {maydon['oxirgi_sugorilgan']}<br>" +
                    f"Tuproq namligi: {maydon['tuproq_namligi']:.1f}%<br>" +
                    f"Status: {holat}<br>" +
                    (f"Ekish sanasi: {ekish_sanasi}<br>" if ekish_sanasi else "") +
                    (f"Pishib yetilish sanasi: {pishib_yetilish_kuni}<br>" if ekish_sanasi else "") +
                    (f"Pishib yetilish holati: {pishib_yetilish_holati}" if ekish_sanasi else ""),
                    max_width=300
                )

                # Maydonni xaritaga qo'shish
                folium.GeoJson(
                    geo_json,
                    style_function=lambda x, rang=rang: {
                        'fillColor': rang,
                        'color': 'white',
                        'weight': 2,
                        'fillOpacity': 0.5,
                        'dashArray': '5, 5'
                    },
                    popup=popup,
                    tooltip=folium.Tooltip(f"{maydon['nomi']} - {holat}")
                ).add_to(xarita_obyekti)

        # Xaritani ko'rsatish
        xarita_data = st_folium(xarita_obyekti, height=500, width="100%",
                                returned_objects=["all_drawings", "last_active_drawing"])

        # Xarita ko'rsatmalari
        st.info("""
        **Xaritada chizish yo'riqnomasi:**
        1. Chap tomondagi chizish vositasini tanlang (chiziq, to'rtburchak yoki ko'pburchak)
        2. Xarita ustida maydonni belgilang
        3. O'ng tomondagi formaga maydon ma'lumotlarini kiriting
        4. "Maydon qo'shish" tugmasini bosing
        5. Maydonni tahrirlash uchun chizish vositalaridan tahrirlash rejimini (▢ belgisi) tanlang
        6. Keyin maydonni o'zgartiring (o'lchamini o'zgartirish, burish)
        """)

    # O'ng ustun - Boshqaruv paneli
    with ong_ustun:
        # Yangi maydon qo'shish formasi
        st.subheader("🌱 Yangi maydon qo'shish")

        nomi = st.text_input("Maydon nomi", key="yangi_nomi")
        ekin_turi = st.selectbox("Ekin turi", list(osimlik_turlari.keys()), key="yangi_ekin")
        oxirgi_sugorilgan = st.date_input("Oxirgi sug'orilgan sana", datetime.date.today(), key="yangi_sana")
        ekish_sanasi = st.date_input("Ekish sanasi", datetime.date.today() - datetime.timedelta(days=30),
                                     key="ekish_sanasi")

        # Ekin turi tanlanganida u haqida ma'lumot ko'rsatish
        if ekin_turi:
            st.info(f"""
            **{ekin_turi.capitalize()} haqida ma'lumot:**
            - Sug'orish davri: {osimlik_turlari[ekin_turi]['sugorish_davri']} kun
            - Pishib yetilish muddati: {osimlik_turlari[ekin_turi]['pishib_yetilish_muddat']} oy
            - Optimal namlik: {osimlik_turlari[ekin_turi]['namlik_optimal']}%
            """)

        tuproq_namligi = st.slider("Tuproq namligi (%)", 0, 100, 50, key="yangi_namlik")

        # Maydonni qo'shish tugmasi
        if st.button("✅ Maydon qo'shish"):
            if xarita_data and 'all_drawings' in xarita_data and xarita_data['all_drawings']:
                shakl = xarita_data['all_drawings'][-1]
                st.session_state.maydonlar.append({
                    "nomi": nomi,
                    "shakl": shakl,
                    "ekin": ekin_turi,
                    "oxirgi_sugorilgan": oxirgi_sugorilgan,
                    "ekish_sanasi": ekish_sanasi,
                    "tuproq_namligi": tuproq_namligi
                })
                st.success(f"{nomi} maydoni muvaffaqiyatli qo'shildi!")
            else:
                st.error("Iltimos, avval xaritada maydon chizing!")

        # Maydonlar ro'yxati
        st.subheader("🌾 Maydonlar ro'yxati")

        # Saralash opsiyasi
        saralash_turi = st.selectbox("Saralash usuli",
                                     ["Nomi bo'yicha", "Ekin turi bo'yicha", "Sug'orish zarurligi bo'yicha",
                                      "Pishib yetilish bo'yicha"])

        if st.session_state.maydonlar:
            # Maydonlarni saralash
            if saralash_turi == "Nomi bo'yicha":
                maydonlar = sorted(st.session_state.maydonlar, key=lambda x: x['nomi'])
            elif saralash_turi == "Ekin turi bo'yicha":
                maydonlar = sorted(st.session_state.maydonlar, key=lambda x: x['ekin'])
            elif saralash_turi == "Sug'orish zarurligi bo'yicha":
                def sugorish_urgentligi(maydon):
                    if maydon["ekin"] not in osimlik_turlari:
                        return 999
                    sugorish_davri = osimlik_turlari[maydon["ekin"]]["sugorish_davri"]
                    sugorishdan_otgan_kunlar = (datetime.date.today() - maydon["oxirgi_sugorilgan"]).days
                    return sugorish_davri - sugorishdan_otgan_kunlar

                maydonlar = sorted(st.session_state.maydonlar, key=sugorish_urgentligi)
            elif saralash_turi == "Pishib yetilish bo'yicha":
                def pishib_yetilish_kunlari(maydon):
                    if "ekish_sanasi" not in maydon or maydon["ekin"] not in osimlik_turlari:
                        return 999
                    pishib_yetilish_muddat = osimlik_turlari[maydon["ekin"]]["pishib_yetilish_muddat"] * 30
                    utgan_kunlar = (datetime.date.today() - maydon["ekish_sanasi"]).days
                    return pishib_yetilish_muddat - utgan_kunlar

                maydonlar = sorted(st.session_state.maydonlar, key=pishib_yetilish_kunlari)
            else:
                maydonlar = st.session_state.maydonlar

            # Maydonlarni ko'rsatish
            for i, maydon in enumerate(maydonlar):
                ekish_sanasi = maydon.get("ekish_sanasi", None)
                rang, holat = maydon_rangini_olish(maydon["oxirgi_sugorilgan"], maydon["ekin"],
                                                   maydon["tuproq_namligi"],
                                                   ekish_sanasi)

                # Har bir maydon uchun kengaytirgich yaratish
                with st.expander(f"{maydon['nomi']} - {holat}", expanded=False):
                    st.write(f"**Ekin:** {maydon['ekin']}")

                    # Pishib yetilish muddatini hisoblash
                    if ekish_sanasi and maydon["ekin"] in osimlik_turlari:
                        pishib_yetilish_muddat = osimlik_turlari[maydon["ekin"]]["pishib_yetilish_muddat"]
                        pishib_yetilish_kuni = ekish_sanasi + datetime.timedelta(days=pishib_yetilish_muddat * 30)
                        qolgan_kunlar = (pishib_yetilish_kuni - datetime.date.today()).days

                        st.write(f"**Ekish sanasi:** {ekish_sanasi}")
                        st.write(f"**Pishib yetilish sanasi:** {pishib_yetilish_kuni}")

                        if qolgan_kunlar > 0:
                            st.write(f"**Pishib yetilishga qolgan vaqt:** {qolgan_kunlar} kun")
                        else:
                            st.write("**Pishib yetilish holati:** Hosilga tayyor")

                    # Sug'orish tugmasi
                    if st.button(f"💧 Sug'orish", key=f"sugorish_{i}"):
                        st.session_state.tanlangan_maydon = i
                        maydonni_sugorish()
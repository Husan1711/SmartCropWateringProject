import streamlit as st
import csv
import datetime
from datetime import timedelta
import pandas as pd
import os

# Ekin bosqichlari o'zbek tiliga tarjimasi
bosqich_tarjimasi = {
    "Germination": "Unib chiqish",
    "Tillering": "Tuplanish",
    "Stem Elongation": "Poya cho'zilishi",
    "Flowering": "Gullash",
    "Maturity": "Pishish",
    "Vegetative": "Vegetativ davr",
    "Tasseling": "So'ta chiqarish",
    "Grain Filling": "Don to'lishi",
    "Seedling": "Ko'chat",
    "Fruiting": "Meva tugish",
    "Pod Development": "Dukkak rivojlanishi",
    "Tubering": "Tugunak hosil qilish",
    "Bulking": "Tugunak to'lishi",
    "Boll Formation": "Ko'sak hosil qilish",
    "Leaf Development": "Barg rivojlanishi",
    "Root Development": "Ildiz rivojlanishi",
    "Sugar Accumulation": "Shakar to'planishi",
    "Pegging": "Yer ostiga kirib borish",
    "Budding": "Kurtak chiqarish",
    "Bulb Development": "Piyoz rivojlanishi",
    "Bulb Formation": "Piyoz hosil qilish",
    "Head Formation": "Bosh hosil qilish",
    "Fruit Development": "Meva rivojlanishi",
    "Fern Development": "O'simta rivojlanishi"
}

# Ekin nomlari o'zbek tiliga tarjimasi
ekin_tarjimasi = {
    "Wheat": "Bug'doy",
    "Corn": "Makkajo'xori",
    "Tomatoes": "Pomidor",
    "Rice": "Guruch",
    "Barley": "Arpa",
    "Soybeans": "Soya",
    "Potatoes": "Kartoshka",
    "Cotton": "Paxta",
    "Sugar Beet": "Qand lavlagi",
    "Peanuts": "Yeryong'oq",
    "Sunflowers": "Kungaboqar",
    "Carrots": "Sabzi",
    "Onions": "Piyoz",
    "Garlic": "Sarimsoq",
    "Spinach": "Ismaloq",
    "Lettuce": "Salat",
    "Broccoli": "Brokoli",
    "Cauliflower": "Gulkaram",
    "Beets": "Lavlagi",
    "Asparagus": "Sarsabil",
    "Cabbage": "Karam",
    "Peppers": "Qalampir",
    "Zucchini": "Qovoqcha",
    "Cucumbers": "Bodring",
    "Pumpkins": "Qovoq",
    "Watermelon": "Tarvuz",
    "Sweet Potatoes": "Batat",
    "Radishes": "Turp",
    "Mint": "Yalpiz",
    "Basil": "Rayhon",
    "Coriander": "Kashnich",
    "Strawberries": "Qulupnay",
    "Blueberries": "Golubika",
    "Raspberries": "Malina",
    "Grapes": "Uzum",
    "Pineapples": "Ananas",
    "Bananas": "Banan",
    "Mangoes": "Mango",
    "Oranges": "Apelsin",
    "Peaches": "Shaftoli",
    "Pears": "Nok",
    "Cherries": "Gilos",
    "Apples": "Olma",
    "Plums": "Olxo'ri",
    "Apricots": "O'rik",
    "Kiwi": "Kivi",
    "Pomegranates": "Anor",
    "Almonds": "Bodom",
    "Olives": "Zaytun",
    "Avocados": "Avokado"
}


def csv_fayldan_oqish(fayl_nomi="sug'orish.csv"):
    """CSV fayldan ma'lumotlarni o'qish"""
    ekinlar_malumoti = {}

    try:
        # First try to find the file in the current directory
        if os.path.exists(fayl_nomi):
            path = fayl_nomi
        # If not found, try the downloads folder
        elif os.path.exists(os.path.join(os.path.expanduser('~'), 'Downloads', fayl_nomi)):
            path = os.path.join(os.path.expanduser('~'), 'Downloads', fayl_nomi)
        # As a fallback, we'll use demo data
        else:
            # If file not found, return some demo data
            return get_demo_data()

        with open(path, 'r', encoding='utf-8') as fayl:
            csv_reader = csv.reader(fayl)
            joriy_ekin = None

            for qator in csv_reader:
                if len(qator) >= 4:  # Kamida 4 ta ustun bo'lishi kerak
                    if qator[1] and qator[1] not in ["Crop", ""]:  # Ekin nomi bo'lsa
                        joriy_ekin = qator[1]
                        ekinlar_malumoti[joriy_ekin] = {"bosqichlar": {}}

                    if joriy_ekin and qator[2] and qator[2] != "Growth Stage":  # O'sish bosqichi bo'lsa
                        # Suv talabi va davomiyligi (masalan: "5-7 mm/day (5-10 days)")
                        suv_malumoti = qator[3] if len(qator) > 3 else ""

                        if suv_malumoti:
                            # Suv talabini ajratib olish (masalan: "5-7 mm/day")
                            suv_talabi = suv_malumoti.split("(")[0].strip()

                            # Davomiylikni ajratib olish (masalan: "5-10 days")
                            davomiylik = suv_malumoti.split("(")[1].replace(")",
                                                                            "").strip() if "(" in suv_malumoti else ""

                            ekinlar_malumoti[joriy_ekin]["bosqichlar"][qator[2]] = {
                                "suv_talabi": suv_talabi,
                                "davomiylik": davomiylik
                            }
        return ekinlar_malumoti
    except Exception as e:
        st.error(f"CSV faylni o'qishda xatolik: {e}")
        # If there's an error, return demo data
        return get_demo_data()


def get_demo_data():
    """Demo ma'lumotlarni qaytaradi agar fayl topilmasa"""
    return {
        "Wheat": {
            "bosqichlar": {
                "Germination": {"suv_talabi": "4-5 mm/day", "davomiylik": "7-10 days"},
                "Tillering": {"suv_talabi": "5-7 mm/day", "davomiylik": "30-40 days"},
                "Stem Elongation": {"suv_talabi": "7-8 mm/day", "davomiylik": "20-30 days"},
                "Flowering": {"suv_talabi": "8-10 mm/day", "davomiylik": "10-15 days"},
                "Grain Filling": {"suv_talabi": "6-8 mm/day", "davomiylik": "15-20 days"},
                "Maturity": {"suv_talabi": "3-4 mm/day", "davomiylik": "10-15 days"}
            }
        },
        "Corn": {
            "bosqichlar": {
                "Germination": {"suv_talabi": "4-6 mm/day", "davomiylik": "5-10 days"},
                "Vegetative": {"suv_talabi": "6-8 mm/day", "davomiylik": "30-40 days"},
                "Tasseling": {"suv_talabi": "8-10 mm/day", "davomiylik": "15-20 days"},
                "Grain Filling": {"suv_talabi": "7-9 mm/day", "davomiylik": "20-30 days"},
                "Maturity": {"suv_talabi": "5-6 mm/day", "davomiylik": "10-15 days"}
            }
        },
        "Tomatoes": {
            "bosqichlar": {
                "Seedling": {"suv_talabi": "3-4 mm/day", "davomiylik": "10-15 days"},
                "Vegetative": {"suv_talabi": "5-6 mm/day", "davomiylik": "20-30 days"},
                "Flowering": {"suv_talabi": "6-8 mm/day", "davomiylik": "15-20 days"},
                "Fruiting": {"suv_talabi": "7-9 mm/day", "davomiylik": "30-45 days"},
                "Maturity": {"suv_talabi": "5-7 mm/day", "davomiylik": "15-20 days"}
            }
        }
    }


def suv_talabini_hisoblash(suv_talabi, maydoni):
    """Suv talabini hisoblash (m³)"""
    # suv_talabi format: "5-7 mm/day"
    if "-" in suv_talabi:
        min_suv, max_suv = map(float, suv_talabi.split(" ")[0].split("-"))
        ortacha_suv = (min_suv + max_suv) / 2  # mm/kun
    else:
        ortacha_suv = float(suv_talabi.split(" ")[0])  # mm/kun

    # mm/kun -> m³/kun/gektar (1 mm = 10 m³/gektar)
    kunlik_suv_m3_gektar = ortacha_suv * 10

    # Umumiy suv hajmi (m³)
    jami_suv_m3 = kunlik_suv_m3_gektar * (maydoni / 10000)  # maydoni m² dan gektarga o'tkaziladi

    return jami_suv_m3


def davomiylikni_hisoblash(davomiylik):
    """Davomiylikni kunlarda hisoblash"""
    # davomiylik format: "5-10 days"
    if "-" in davomiylik:
        min_kun, max_kun = map(int, davomiylik.split(" ")[0].split("-"))
        ortacha_kun = (min_kun + max_kun) / 2
    else:
        ortacha_kun = int(davomiylik.split(" ")[0])

    return ortacha_kun


def keyingi_sugorish_kuni(oxirgi_sugorish_kuni, bosqich_davomiyligi):
    """Keyingi sug'orish kunini hisoblash"""
    keyingi_sana = oxirgi_sugorish_kuni + timedelta(days=bosqich_davomiyligi)
    return keyingi_sana


def main():
    # Streamlit dasturi sarlavhasi
    st.title("Ekinlarni Sug'orish Dasturi")

    # Custom styling to match app.py
    st.markdown("""
    <style>
        .main {
            background-color: #e8f5e9 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # CSV fayldan ma'lumotlarni o'qish
    ekinlar_malumoti = csv_fayldan_oqish()

    # Agar ma'lumotlar mavjud bo'lsa
    if ekinlar_malumoti:
        # Ekin turini tanlash
        st.header("1. Ekin Turini Tanlash")

        mavjud_ekinlar = list(ekinlar_malumoti.keys())
        ekin_tanlash_options = [f"{ekin} - {ekin_tarjimasi.get(ekin, ekin)}" for ekin in mavjud_ekinlar]

        selected_ekin_option = st.selectbox("Ekin turini tanlang:", ekin_tanlash_options)
        tanlangan_ekin = mavjud_ekinlar[ekin_tanlash_options.index(selected_ekin_option)]

        # O'sish bosqichini tanlash
        st.header("2. O'sish Bosqichini Tanlash")

        mavjud_bosqichlar = list(ekinlar_malumoti[tanlangan_ekin]["bosqichlar"].keys())
        bosqich_tanlash_options = [f"{bosqich} - {bosqich_tarjimasi.get(bosqich, bosqich)}" for bosqich in
                                   mavjud_bosqichlar]

        selected_bosqich_option = st.selectbox("O'sish bosqichini tanlang:", bosqich_tanlash_options)
        tanlangan_bosqich = mavjud_bosqichlar[bosqich_tanlash_options.index(selected_bosqich_option)]

        # Oxirgi sug'orilgan sana
        st.header("3. Oxirgi Sug'orish Sanasi")

        oxirgi_sugorish = st.date_input("Oxirgi sug'orilgan sana:", datetime.datetime.now())

        # Yer maydoni
        st.header("4. Yer Maydoni")

        maydon = st.number_input("Yer maydonini kiriting (m²):", min_value=1.0, value=1000.0, step=100.0)

        # Hisoblash tugmasi
        if st.button("Hisoblash", key="hisoblash"):
            # Hisob-kitoblar
            bosqich_malumoti = ekinlar_malumoti[tanlangan_ekin]["bosqichlar"][tanlangan_bosqich]

            suv_talabi = bosqich_malumoti["suv_talabi"]
            davomiylik = bosqich_malumoti["davomiylik"]

            # Hisoblash
            kunlik_suv = suv_talabini_hisoblash(suv_talabi, maydon)
            bosqich_davomiyligi = davomiylikni_hisoblash(davomiylik)
            keyingi_sana = keyingi_sugorish_kuni(oxirgi_sugorish, bosqich_davomiyligi)

            # Natijalarni ko'rsatish
            st.subheader("Hisob-kitob Natijalari:")
            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Ekin Ma'lumotlari:")
                st.write(f"**Ekin:** {tanlangan_ekin} ({ekin_tarjimasi.get(tanlangan_ekin, tanlangan_ekin)})")
                st.write(
                    f"**O'sish bosqichi:** {tanlangan_bosqich} ({bosqich_tarjimasi.get(tanlangan_bosqich, tanlangan_bosqich)})")
                st.write(f"**Suv talabi:** {suv_talabi}")
                st.write(f"**Bosqich davomiyligi:** {davomiylik}")

            with col2:
                st.markdown("### Sug'orish Ma'lumotlari:")
                st.write(f"**Yer maydoni:** {maydon} m²")
                st.write(f"**Kunlik suv sarfi:** {kunlik_suv:.2f} m³")
                st.write(f"**Umumiy bosqich uchun suv sarfi:** {kunlik_suv * bosqich_davomiyligi:.2f} m³")
                st.write(f"**Keyingi sug'orish kuni:** {keyingi_sana.strftime('%d.%m.%Y')}")

            # Qo'shimcha ma'lumotlar uchun grafik va jadval
            st.markdown("---")
            st.subheader("Sug'orish Jadvali:")

            # Keyingi 5 ta sug'orish sanasi
            sugorish_jadvali = []
            joriy_sana = oxirgi_sugorish

            for i in range(5):
                joriy_sana = keyingi_sugorish_kuni(joriy_sana, bosqich_davomiyligi)
                sugorish_jadvali.append({
                    "Tartib": i + 1,
                    "Sana": joriy_sana.strftime('%d.%m.%Y'),
                    "Suv miqdori (m³)": f"{kunlik_suv * bosqich_davomiyligi:.2f}"
                })

            st.table(pd.DataFrame(sugorish_jadvali))

            # Jadval haqida izoh
            st.info(
                "Yuqoridagi jadvalda keyingi 5 ta sug'orish sanasi va har bir sug'orish uchun zarur bo'lgan suv miqdori ko'rsatilgan."
            )
    else:
        st.error("\"sug'orish.csv\" fayli topilmadi yoki to'g'ri formatda emas.")
        st.info("""
        ### CSV fayl quyidagi formatda bo'lishi kerak:

        ```
        No,Crop,Growth Stage,Water Requirement
        1,Wheat,Germination,4-5 mm/day (7-10 days)
        2,Wheat,Tillering,5-7 mm/day (30-40 days)
        ...
        ```

        CSV faylini dastur bilan bir papkada \"sug'orish.csv\" nomi bilan saqlang.
        """)


if __name__ == "__main__":
    main()
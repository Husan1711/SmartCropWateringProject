import streamlit as st
import sys
import os
import importlib.util

# Sahifa konfiguratsiyasi
st.set_page_config(
    page_title="SmartCropWatering",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stillar
st.markdown("""
<style>
    .main {
        background-color: #e8f5e9 !important;
        color: #1e1e1e !important;
    }
    .stApp {
        background-color: #e8f5e9 !important;
    }
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #c8e6c9 !important;
    }
    .css-1a32fsj, .css-6qob1r {
        background-color: #a5d6a7 !important;
    }
    .css-1v3fvcr {
        background-color: #c8e6c9 !important;
        color: #1e1e1e !important;
    }
    .nav-icon-container {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .nav-icon {
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        margin-right: 12px;
        font-size: 18px;
    }
    .stButton > button {
        background-color: #a5d6a7;
        color: #1e1e1e;
        border: none;
        border-radius: 8px;
        text-align: left;
        width: 100%;
        transition: all 0.3s ease;
    }
    .obhavo-button:hover {
        box-shadow: 0 0 25px 5px rgba(66, 133, 244, 0.6) !important;
        transform: scale(1.05) !important;
        background-color: #81c784 !important;
    }
    .xarita-button:hover {
        box-shadow: 0 0 25px 5px rgba(234, 67, 53, 0.6) !important;
        transform: scale(1.05) !important;
        background-color: #81c784 !important;
    }
    .osimlik-button:hover {
        box-shadow: 0 0 25px 5px rgba(52, 168, 83, 0.6) !important;
        transform: scale(1.05) !important;
        background-color: #81c784 !important;
    }
    .intellektual-button:hover {
        box-shadow: 0 0 25px 5px rgba(251, 188, 5, 0.6) !important;
        transform: scale(1.05) !important;
        background-color: #81c784 !important;
    }
    .crop-button:hover {
        box-shadow: 0 0 25px 5px rgba(156, 39, 176, 0.6) !important;
        transform: scale(1.05) !important;
        background-color: #81c784 !important;
    }
    .disease-button:hover {
        box-shadow: 0 0 25px 5px rgba(255, 87, 34, 0.6) !important;
        transform: scale(1.05) !important;
        background-color: #81c784 !important;
    }
    .ai-button:hover {
        box-shadow: 0 0 25px 5px rgba(0, 150, 136, 0.6) !important;
        transform: scale(1.05) !important;
        background-color: #81c784 !important;
    }
</style>
""", unsafe_allow_html=True)


# Modullar uchun placeholder klasslar

# Ob-havo uchun placeholder
class WeatherPlaceholder:
    def show_weather_page():
        st.error("Ob-havo ma'lumotlari moduli topilmadi. Iltimos, weather.py faylini tekshiring.")


# Xarita uchun placeholder
class Xarita2Placeholder:
    def show_xarita_page():
        st.error("Xarita moduli topilmadi. Iltimos, xarita2.py faylini tekshiring.")


# Ekinlar uchun placeholder
class CropPlaceholder:
    def main():
        st.error("Ekinlar ma'lumotlar moduli topilmadi. Iltimos, crop.py faylini tekshiring.")


# Kasalliklar uchun placeholder
class DiseaseaiPlaceholder:
    def main():
        st.error("Kasalliklarni aniqlash moduli topilmadi. Iltimos, diseaseai.py faylini tekshiring.")


# AI xulosa uchun placeholder
class SmartIrrigationAIPlaceholder:
    def show_ai_results():
        st.error("AI xulosa moduli topilmadi. Iltimos, smart_irrigation_ai.py faylini tekshiring.")

    def register_page():
        return SmartIrrigationAIPlaceholder.show_ai_results


# Modullarni import qilish
try:
    import weather
except ImportError:
    weather = WeatherPlaceholder

try:
    import xarita2
except ImportError:
    xarita2 = Xarita2Placeholder

try:
    import crop
except ImportError:
    crop = CropPlaceholder

# diseaseai modulini import qilish
try:
    # Normal import usuli
    import diseaseai
except ImportError:
    # Agar import qilishda xatolik bo'lsa, faylni to'g'ridan-to'g'ri yuklab ko'ramiz
    try:
        # Joriy papkani olish
        current_dir = os.path.dirname(os.path.abspath(__file__))
        diseaseai_path = os.path.join(current_dir, "diseaseai.py")

        # Fayl mavjudligini tekshirish
        if os.path.exists(diseaseai_path):
            # Fayl mavjud bo'lsa, uni modulga aylantiramiz
            spec = importlib.util.spec_from_file_location("diseaseai", diseaseai_path)
            if spec:
                diseaseai = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(diseaseai)
            else:
                diseaseai = DiseaseaiPlaceholder
        else:
            diseaseai = DiseaseaiPlaceholder
    except Exception:
        diseaseai = DiseaseaiPlaceholder

# smart_irrigation_ai modulini import qilish
try:
    # Normal import usuli
    from smart_irrigation_ai import register_page as ai_register_page
except ImportError:
    # Agar import qilishda xatolik bo'lsa, faylni to'g'ridan-to'g'ri yuklab ko'ramiz
    try:
        # Joriy papkani olish
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ai_path = os.path.join(current_dir, "smart_irrigation_ai.py")

        # Fayl mavjudligini tekshirish
        if os.path.exists(ai_path):
            # Fayl mavjud bo'lsa, uni modulga aylantiramiz
            spec = importlib.util.spec_from_file_location("smart_irrigation_ai", ai_path)
            if spec:
                smart_irrigation_ai = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(smart_irrigation_ai)
                ai_register_page = smart_irrigation_ai.register_page
            else:
                ai_register_page = SmartIrrigationAIPlaceholder.register_page
        else:
            ai_register_page = SmartIrrigationAIPlaceholder.register_page
    except Exception:
        ai_register_page = SmartIrrigationAIPlaceholder.register_page

# Session state ni o'rnatish
if 'active_nav' not in st.session_state:
    st.session_state.active_nav = "intellektual"  # Boshlang'ich sahifa

# Sidebar yaratish
with st.sidebar:
    st.markdown(
        "<div style='text-align: center; color: #1e1e1e; padding: 15px 0; font-size: 18px; font-weight: 600; border-bottom: 1px solid rgba(0,0,0,0.1); margin-bottom: 20px;'>Navigatsiya</div>",
        unsafe_allow_html=True)

    # Ob-havo tugmasi
    st.markdown("<div id='obhavo-container' class='obhavo-button'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("<div class='nav-icon' style='background-color: rgba(66, 133, 244, 0.2); color: #4285f4;'>🌤️</div>",
                    unsafe_allow_html=True)
    with col2:
        obhavo = st.button("Ob-havo ma'lumotlari", key="obhavo", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Xarita tugmasi
    st.markdown("<div id='xarita-container' class='xarita-button'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("<div class='nav-icon' style='background-color: rgba(234, 67, 53, 0.2); color: #ea4335;'>🗺️</div>",
                    unsafe_allow_html=True)
    with col2:
        xarita = st.button("Xarita va tuproq namligi", key="xarita", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # # O'simlik tugmasi
    # st.markdown("<div id='osimlik-container' class='osimlik-button'>", unsafe_allow_html=True)
    # col1, col2 = st.columns([1, 4])
    # with col1:
    #     st.markdown("<div class='nav-icon' style='background-color: rgba(52, 168, 83, 0.2); color: #34a853;'>🌱</div>",
    #                 unsafe_allow_html=True)
    # with col2:
    #     osimlik = st.button("O'simliklar bo'yicha ma'lumotlar", key="osimlik", use_container_width=True)
    # st.markdown("</div>", unsafe_allow_html=True)

    # Ekinlarni sug'orish tugmasi
    st.markdown("<div id='crop-container' class='crop-button'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("<div class='nav-icon' style='background-color: rgba(156, 39, 176, 0.2); color: #9c27b0;'>💧</div>",
                    unsafe_allow_html=True)
    with col2:
        crop_watering = st.button("Ekinlarni Sug'orishini Hisoblash", key="crop", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Kasallikni aniqlash tugmasi
    st.markdown("<div id='disease-container' class='disease-button'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("<div class='nav-icon' style='background-color: rgba(255, 87, 34, 0.2); color: #ff5722;'>🔬</div>",
                    unsafe_allow_html=True)
    with col2:
        disease_detection = st.button("Kasallikni aniqlash va davolash", key="disease", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Intellektual tugmasi
    st.markdown("<div id='intellektual-container' class='intellektual-button'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("<div class='nav-icon' style='background-color: rgba(251, 188, 5, 0.2); color: #fbbc05;'>🧠</div>",
                    unsafe_allow_html=True)
    with col2:
        intellektual = st.button("Intellektual tavsiyalar", key="intellektual", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # AI XULOSA tugmasi - YANGI
    st.markdown("<div id='ai-container' class='ai-button'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("<div class='nav-icon' style='background-color: rgba(0, 150, 136, 0.2); color: #009688;'>🤖</div>",
                    unsafe_allow_html=True)
    with col2:
        ai_xulosa = st.button("AI XULOSA", key="ai_xulosa", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Hover effektlari uchun JavaScript
    st.markdown("""
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const buttons = document.querySelectorAll('.stButton > button');
        buttons.forEach(button => {
            button.addEventListener('mouseover', function() {
                let parent = this.closest('div[id$="-container"]');
                if (parent) {
                    parent.classList.add('hover');
                }
            });

            button.addEventListener('mouseout', function() {
                let parent = this.closest('div[id$="-container"]');
                if (parent) {
                    parent.classList.remove('hover');
                }
            });
        });
    });
    </script>
    """, unsafe_allow_html=True)

# Tugmalar orqali navigatsiyani boshqarish
if obhavo:
    st.session_state.active_nav = "obhavo"
elif xarita:
    st.session_state.active_nav = "xarita"
# elif osimlik:
#     st.session_state.active_nav = "osimlik"
elif crop_watering:
    st.session_state.active_nav = "crop"
elif disease_detection:
    st.session_state.active_nav = "disease"
elif intellektual:
    st.session_state.active_nav = "intellektual"
elif ai_xulosa:  # YANGI - AI xulosa tugmasi uchun
    st.session_state.active_nav = "ai_xulosa"

# Tanlangan navigatsiyaga mos sahifani ko'rsatish
if st.session_state.active_nav == "obhavo":
    try:
        # Modulni yangilash
        if 'weather' in sys.modules:
            importlib.reload(sys.modules['weather'])
        # Ob-havo sahifasini ko'rsatish
        weather.show_weather_page()
    except Exception as e:
        st.error(f"Ob-havo sahifasini yuklashda xatolik: {e}")

elif st.session_state.active_nav == "xarita":
    try:
        # Modulni yangilash
        if 'xarita2' in sys.modules:
            importlib.reload(sys.modules['xarita2'])
        # Xarita sahifasini ko'rsatish
        xarita2.show_xarita_page()
    except Exception as e:
        st.error(f"Xarita sahifasini yuklashda xatolik: {e}")

elif st.session_state.active_nav == "osimlik":
    st.title("O'simliklar bo'yicha ma'lumotlar")
    st.info("Bu sahifa ishlab chiqish jarayonida...")

elif st.session_state.active_nav == "crop":
    try:
        # Modulni yangilash
        if 'crop' in sys.modules:
            importlib.reload(sys.modules['crop'])
        # Ekinlar sahifasini ko'rsatish
        crop.main()
    except Exception as e:
        st.error(f"Ekinlarni Sug'orish sahifasini yuklashda xatolik: {e}")

elif st.session_state.active_nav == "disease":
    try:
        # Modulni yangilash
        if 'diseaseai' in sys.modules:
            importlib.reload(sys.modules['diseaseai'])
        # Kasalliklarni aniqlash sahifasini ko'rsatish
        if hasattr(diseaseai, 'main'):
            diseaseai.main()
        else:
            st.error("diseaseai modulida main() funksiyasi topilmadi!")
    except Exception as e:
        st.error(f"Kasalliklarni aniqlash sahifasini yuklashda xatolik: {e}")

elif st.session_state.active_nav == "intellektual":
    st.title("Intellektual tavsiyalar")
    st.info("Bu sahifa ishlab chiqish jarayonida...")

# YANGI - AI XULOSA sahifasi
elif st.session_state.active_nav == "ai_xulosa":
    try:
        # AI xulosa sahifasini ko'rsatish
        ai_page = ai_register_page()
        ai_page()
    except Exception as e:
        st.error(f"AI XULOSA sahifasini yuklashda xatolik: {e}")
        st.exception(e)

# Footer
st.markdown("""
<div style="position: fixed; bottom: 10px; width: 100%; text-align: center; color: #1e1e1e; font-size: 10px;">
    © 2025 Aqlli Dehqonchilik
</div>
""", unsafe_allow_html=True)
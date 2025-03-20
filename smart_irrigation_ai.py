import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import time
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go

# Existing modules import
# Note: We've removed the direct import of analyze_plant_image since it doesn't exist
from weather import get_forecast, show_weather
from xarita2 import maydon_rangini_olish, osimlik_turlari
# No direct import from diseaseai
from crop import suv_talabini_hisoblash, davomiylikni_hisoblash, keyingi_sugorish_kuni

# O'zbekiston viloyatlari
UZB_VILOYATLAR = {
    "Toshkent": "Tashkent",
    "Samarqand": "Samarkand",
    "Buxoro": "Bukhara",
    "Farg'ona": "Fergana",
    "Andijon": "Andijan",
    "Namangan": "Namangan",
    "Navoiy": "Navoi",
    "Xorazm": "Khorezm",
    "Qashqadaryo": "Kashkadarya",
    "Surxondaryo": "Surkhandarya",
    "Jizzax": "Jizzakh",
    "Sirdaryo": "Syrdarya",
    "Qoraqalpog'iston": "Karakalpakstan"
}

# Ekin turlari ro'yxati
EKIN_TURLARI = [
    "bug'doy",
    "makkajo'xori",
    "sholi",
    "paxta",
    "sabzavotlar",
    "kartoshka",
    "beda",
    "pomidor",
    "bodring"
]


# Weather factors that affect irrigation
def analyze_weather_forecast(region):
    """
    Analyze weather forecast to get monthly average temperature and precipitation probability
    Args:
        region: Selected region name
    Returns:
        Dictionary with avg_temp, avg_rain_prob
    """
    try:
        forecast_data = get_forecast(region)
        if forecast_data:
            # Calculate monthly averages
            avg_temp = forecast_data["weekly_avg_temp"]  # Using weekly as an approximation
            avg_rain_prob = forecast_data["weekly_avg_rain_prob"]

            # Prepare daily data for visualization
            dates = [date.strftime("%d-%m") for date in forecast_data["daily_dates"]]
            temps = forecast_data["daily_temps"]
            rain_probs = forecast_data["daily_rain_probs"]

            return {
                "avg_temp": avg_temp,
                "avg_rain_prob": avg_rain_prob,
                "dates": dates,
                "temps": temps,
                "rain_probs": rain_probs,
                "status": "success"
            }
        else:
            return {"status": "error", "message": "Ob-havo ma'lumotlari olinmadi"}
    except Exception as e:
        return {"status": "error", "message": f"Ob-havo tahlili xatosi: {str(e)}"}


# Field status analysis
def analyze_field_status(field_data):
    """
    Analyze field data to get soil moisture, crop type, last irrigation date
    Args:
        field_data: Dictionary with field information
    Returns:
        Dictionary with analysis results
    """
    try:
        crop_type = field_data.get("ekin", "")
        last_irrigated = field_data.get("oxirgi_sugorilgan", datetime.date.today())
        soil_moisture = field_data.get("tuproq_namligi", 50)
        planting_date = field_data.get("ekish_sanasi", None)

        if crop_type in osimlik_turlari:
            crop_info = osimlik_turlari[crop_type]
            irrigation_period = crop_info["sugorish_davri"]
            optimal_moisture = crop_info["namlik_optimal"]
            min_moisture = crop_info["namlik_minimum"]

            days_since_irrigation = (datetime.date.today() - last_irrigated).days

            # Calculate irrigation urgency
            if soil_moisture < min_moisture:
                urgency = "high"
                urgency_score = 3
            elif soil_moisture < min_moisture * 1.2:
                urgency = "medium"
                urgency_score = 2
            else:
                urgency = "low"
                urgency_score = 1

            # Calculate next irrigation date based on period
            next_irrigation_date = last_irrigated + datetime.timedelta(days=irrigation_period)
            days_to_next = (next_irrigation_date - datetime.date.today()).days

            return {
                "crop_type": crop_type,
                "last_irrigated": last_irrigated,
                "soil_moisture": soil_moisture,
                "optimal_moisture": optimal_moisture,
                "min_moisture": min_moisture,
                "days_since_irrigation": days_since_irrigation,
                "next_scheduled_irrigation": next_irrigation_date,
                "days_to_next_irrigation": days_to_next,
                "irrigation_urgency": urgency,
                "urgency_score": urgency_score,
                "irrigation_period": irrigation_period,
                "status": "success"
            }
        else:
            return {"status": "error", "message": "Ekin turi tanlanmagan yoki noto'g'ri"}
    except Exception as e:
        return {"status": "error", "message": f"Dalani tahlil qilishda xatolik: {str(e)}"}


# Disease analysis - rewritten to not depend on the missing function
def analyze_disease_status(disease_info):
    """
    Analyze if plant has disease and if it affects irrigation
    Args:
        disease_info: Dictionary with disease information
    Returns:
        Dictionary with analysis results
    """
    try:
        if not disease_info or "name" not in disease_info:
            return {
                "has_disease": False,
                "irrigation_adjustment": 0,
                "status": "success",
                "message": "Kasallik ma'lumotlari mavjud emas"
            }

        # Common diseases that require reduced irrigation
        reduce_water_diseases = [
            "fitoftoroz", "bakterial_rak", "bakterial_dog", "qora_chirish",
            "fuzarioz", "bakterial_chirish", "so'lish", "un_shudring"
        ]

        # Check if disease name contains any keywords that suggest reducing water
        disease_name = disease_info.get("name", "").lower()
        needs_reduced_water = any(disease in disease_name for disease in reduce_water_diseases)

        # Calculate irrigation adjustment (-30% for water-sensitive diseases)
        irrigation_adjustment = -0.3 if needs_reduced_water else 0

        return {
            "has_disease": True,
            "disease_name": disease_info.get("name", ""),
            "requires_reduced_water": needs_reduced_water,
            "irrigation_adjustment": irrigation_adjustment,
            "recommendations": disease_info.get("treatment", ""),
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": f"Kasallik tahlilida xatolik: {str(e)}"}


# Crop water requirements analysis
def analyze_crop_water_needs(crop_data):
    """
    Analyze crop water requirements based on growth stage
    Args:
        crop_data: Dictionary with crop information
    Returns:
        Dictionary with water requirements
    """
    try:
        crop_type = crop_data.get("crop_type", "")
        growth_stage = crop_data.get("growth_stage", "")
        area = crop_data.get("area", 1000)  # m²

        # Get water requirements from crop.py functions
        water_req_text = crop_data.get("water_requirement", "5-7 mm/day")
        duration_text = crop_data.get("duration", "7-10 days")

        # Calculate water requirements
        daily_water = suv_talabini_hisoblash(water_req_text, area)
        stage_duration = davomiylikni_hisoblash(duration_text)

        return {
            "crop_type": crop_type,
            "growth_stage": growth_stage,
            "area": area,
            "daily_water_requirement": daily_water,
            "stage_duration": stage_duration,
            "total_stage_water": daily_water * stage_duration,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": f"Ekin suv ehtiyojini tahlil qilishda xatolik: {str(e)}"}


# Smart irrigation scheduling
def calculate_smart_irrigation(weather_data, field_data, disease_data, crop_data):
    """
    Calculate smart irrigation schedule based on all factors
    Args:
        weather_data: Weather forecast analysis
        field_data: Field status analysis
        disease_data: Disease analysis
        crop_data: Crop water needs analysis
    Returns:
        Dictionary with irrigation schedule and recommendations
    """
    try:
        # Base water requirement
        base_daily_water = crop_data.get("daily_water_requirement", 0)
        base_irrigation_interval = field_data.get("days_to_next_irrigation", 7)

        # Weather adjustment factors
        temp_adjustment = 0
        rain_adjustment = 0

        # Adjust for temperature
        avg_temp = weather_data.get("avg_temp", 25)
        if avg_temp > 30:
            temp_adjustment = 0.2  # Increase water by 20% for hot weather
        elif avg_temp < 15:
            temp_adjustment = -0.1  # Decrease water by 10% for cool weather

        # Adjust for rain probability
        avg_rain_prob = weather_data.get("avg_rain_prob", 0)
        if avg_rain_prob > 70:
            rain_adjustment = -0.3  # Decrease water by 30% if high rain probability
        elif avg_rain_prob > 40:
            rain_adjustment = -0.15  # Decrease water by 15% if medium rain probability

        # Disease adjustment
        disease_adjustment = disease_data.get("irrigation_adjustment", 0)

        # Soil moisture urgency adjustment
        urgency_score = field_data.get("urgency_score", 2)
        urgency_adjustment = 0
        if urgency_score == 3:  # High urgency
            urgency_adjustment = 0.1  # Increase water by 10%
            base_irrigation_interval = 0  # Irrigate immediately
        elif urgency_score == 1:  # Low urgency
            urgency_adjustment = -0.1  # Decrease water by 10%

        # Calculate final adjustments
        total_adjustment = 1 + temp_adjustment + rain_adjustment + disease_adjustment + urgency_adjustment
        adjusted_water = base_daily_water * total_adjustment

        # Generate irrigation schedule
        start_date = datetime.date.today()
        if base_irrigation_interval > 0:
            start_date = start_date + datetime.timedelta(days=base_irrigation_interval)

        schedule = []
        detailed_schedule = []
        current_date = start_date

        # Generate schedule for next 5 irrigations
        for i in range(5):
            # Adjust water amount based on the forecast for that specific day
            day_adjustment = 1.0
            temp_day_adj = 0
            rain_day_adj = 0

            # Check if we have forecast data for this day
            day_idx = min(i, len(weather_data.get("dates", [])) - 1)
            if day_idx >= 0:
                day_temp = weather_data.get("temps", [])[day_idx] if day_idx < len(
                    weather_data.get("temps", [])) else avg_temp
                day_rain_prob = weather_data.get("rain_probs", [])[day_idx] if day_idx < len(
                    weather_data.get("rain_probs", [])) else avg_rain_prob

                # Adjust for that day's temperature
                if day_temp > 30:
                    temp_day_adj = 0.15
                elif day_temp < 15:
                    temp_day_adj = -0.1

                # Adjust for that day's rain probability
                if day_rain_prob > 70:
                    rain_day_adj = -0.4
                elif day_rain_prob > 40:
                    rain_day_adj = -0.2

                # Combined daily adjustment
                day_adjustment = 1.0 + temp_day_adj + rain_day_adj

            # Calculate water amount for this irrigation
            water_amount = adjusted_water * day_adjustment

            # Base water without adjustments (for comparison)
            base_water = base_daily_water

            # Add to schedule
            schedule.append({
                "irrigation_number": i + 1,
                "date": current_date,
                "water_amount": max(0, water_amount),  # Ensure non-negative
                "adjustment_factor": day_adjustment,
                "temperature": weather_data.get("temps", [])[day_idx] if day_idx < len(
                    weather_data.get("temps", [])) else None,
                "rain_probability": weather_data.get("rain_probs", [])[day_idx] if day_idx < len(
                    weather_data.get("rain_probs", [])) else None
            })

            # Add to detailed schedule with individual adjustment factors
            detailed_schedule.append({
                "irrigation_number": i + 1,
                "date": current_date,
                "base_water": base_water,
                "final_water": max(0, water_amount),
                "temperature": day_temp if day_idx < len(weather_data.get("temps", [])) else None,
                "temp_adjustment": temp_day_adj,
                "temp_effect": base_water * temp_day_adj,
                "rain_probability": day_rain_prob if day_idx < len(weather_data.get("rain_probs", [])) else None,
                "rain_adjustment": rain_day_adj,
                "rain_effect": base_water * rain_day_adj,
                "disease_adjustment": disease_adjustment,
                "disease_effect": base_water * disease_adjustment,
                "soil_adjustment": urgency_adjustment,
                "soil_effect": base_water * urgency_adjustment,
                "total_adjustment": day_adjustment + disease_adjustment + urgency_adjustment - 1.0,
                "total_effect": water_amount - base_water
            })

            # Move to next irrigation date based on crop needs
            interval = field_data.get("irrigation_period", 7)
            current_date = current_date + datetime.timedelta(days=interval)

        # Generate recommendations
        recommendations = []

        if temp_adjustment > 0:
            recommendations.append("🌡️ Harorat yuqori bo'lgani uchun sug'orish miqdori oshirildi")

        if rain_adjustment < 0:
            recommendations.append("🌧️ Yomg'ir ehtimoli yuqori bo'lgani uchun sug'orish miqdori kamaytirildi")

        if disease_data.get("requires_reduced_water", False):
            recommendations.append(
                f"🦠 {disease_data.get('disease_name')} kasalligi tufayli sug'orish miqdori kamaytirildi")

        if urgency_score == 3:
            recommendations.append("⚠️ Tuproq namligi juda past, tezda sug'orish tavsiya etiladi")

        return {
            "base_water_requirement": base_daily_water,
            "adjusted_water_requirement": adjusted_water,
            "temperature_adjustment": temp_adjustment,
            "rain_adjustment": rain_adjustment,
            "disease_adjustment": disease_adjustment,
            "soil_urgency_adjustment": urgency_adjustment,
            "total_adjustment_factor": total_adjustment,
            "schedule": schedule,
            "detailed_schedule": detailed_schedule,
            "recommendations": recommendations,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": f"Aqlli sug'orish jadvalini hisoblashda xatolik: {str(e)}"}


def show_ai_results():
    """
    Main function to display AI irrigation analysis page
    """
    st.title("🤖 Aqlli Sug'orish AI Xulosasi")

    # Apply some styling
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #2e7d32;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: 700;
        }
        .result-box {
            background-color: #f1f8e9;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            border-left: 5px solid #7cb342;
        }
        .info-box {
            background-color: #e8f5e9;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            border-left: 5px solid #4caf50;
        }
        .warning-box {
            background-color: #fff8e1;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            border-left: 5px solid #ffc107;
        }
        .error-box {
            background-color: #ffebee;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            border-left: 5px solid #f44336;
        }
        .adjustment-positive {
            color: #2e7d32;
            font-weight: bold;
        }
        .adjustment-negative {
            color: #c62828;
            font-weight: bold;
        }
        .adjustment-neutral {
            color: #757575;
            font-weight: bold;
        }
        table {
            font-size: 14px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Create tabs for different analysis views
    tab1, tab2, tab3 = st.tabs(["📊 Sug'orish Tahlili", "🌱 Qo'shimcha Ma'lumotlar", "ℹ️ Yordam"])

    with tab1:
        st.subheader("Sug'orish rejasini yaratish")

        # Create columns for selection inputs
        col1, col2 = st.columns(2)

        with col1:
            # Select region for weather data - now with full list of regions
            selected_region = st.selectbox(
                "Viloyatni tanlang:",
                list(UZB_VILOYATLAR.keys()),
                index=0
            )

            # Select field for analysis
            if "maydonlar" in st.session_state and len(st.session_state.maydonlar) > 0:
                fields = [field["nomi"] for field in st.session_state.maydonlar]
                selected_field_name = st.selectbox("Maydonni tanlang:", fields)

                # Get the selected field data
                selected_field = next(
                    (field for field in st.session_state.maydonlar if field["nomi"] == selected_field_name), None)
            else:
                # Demo field if not available
                st.info("Maydonlar topilmadi. Namunali ma'lumotlar ishlatiladi.")
                today = datetime.date.today()

                # Here we prompt user to select crop type instead of hardcoding
                selected_crop_type = st.selectbox(
                    "Ekin turini tanlang:",
                    EKIN_TURLARI,
                    index=0
                )

                selected_field = {
                    "nomi": "Namunali maydon",
                    "ekin": selected_crop_type,
                    "oxirgi_sugorilgan": today - datetime.timedelta(days=5),
                    "ekish_sanasi": today - datetime.timedelta(days=30),
                    "tuproq_namligi": 40
                }

        with col2:
            # Growth stage selection for crop data
            if selected_field and "ekin" in selected_field:
                crop_type = selected_field["ekin"]

                growth_stages = ["Unib chiqish", "Tuplanish", "Poya cho'zilishi", "Gullash", "Don to'lishi", "Pishish"]
                selected_stage = st.selectbox("O'sish bosqichini tanlang:", growth_stages)

                # Water requirement mapping based on growth stage
                water_requirements = {
                    "Unib chiqish": "4-5 mm/day (7-10 days)",
                    "Tuplanish": "5-7 mm/day (20-30 days)",
                    "Poya cho'zilishi": "7-8 mm/day (15-20 days)",
                    "Gullash": "8-10 mm/day (10-15 days)",
                    "Don to'lishi": "6-8 mm/day (15-20 days)",
                    "Pishish": "3-4 mm/day (10-15 days)"
                }

                # Get water requirement for selected stage
                water_req = water_requirements.get(selected_stage, "5-7 mm/day (10-15 days)")
                water_req_value = water_req.split(" ")[0]
                duration_value = water_req.split("(")[1].replace(")", "")

                # Area input
                area = st.number_input("Maydon o'lchami (m²):", min_value=1.0, value=1000.0, step=100.0)
            else:
                st.warning("Ekin turi mavjud emas!")
                crop_type = ""
                selected_stage = ""
                water_req = "5-7 mm/day (10-15 days)"
                water_req_value = "5-7 mm/day"
                duration_value = "10-15 days"
                area = 1000.0

        # Disease checkbox
        has_disease = st.checkbox("Ekinlarda kasallik bormi?")

        if has_disease:
            disease_options = [
                "Fitoftoroz", "Barg dog'lanishi", "Bakterial dog'lanish",
                "Un shudring", "Bakterial chirish", "Fuzarioz"
            ]
            selected_disease = st.selectbox("Kasallik turini tanlang:", disease_options)

            # Create simple disease info object
            disease_info = {
                "name": selected_disease,
                "treatment": "Maxsus fungitsid bilan ishlov bering va sug'orishni kamaytiring."
            }
        else:
            disease_info = {
                "name": "Sog'lom o'simlik",
                "treatment": "Davolash talab etilmaydi."
            }

        # Analysis button
        if st.button("🔍 Tahlil qilish", use_container_width=True):
            with st.spinner("Ma'lumotlar tahlil qilinmoqda..."):
                # Progress bar for better UX
                progress_bar = st.progress(0)

                # 1. Analyze weather data
                progress_bar.progress(20)
                weather_data = analyze_weather_forecast(selected_region)

                # 2. Analyze field status
                progress_bar.progress(40)
                field_data = analyze_field_status(selected_field)

                # 3. Analyze disease status
                progress_bar.progress(60)
                disease_data = analyze_disease_status(disease_info)

                # 4. Analyze crop water needs
                progress_bar.progress(80)
                crop_data = {
                    "crop_type": crop_type,
                    "growth_stage": selected_stage,
                    "area": area,
                    "water_requirement": water_req_value,
                    "duration": duration_value
                }
                crop_analysis = analyze_crop_water_needs(crop_data)

                # 5. Calculate smart irrigation schedule
                progress_bar.progress(100)
                time.sleep(0.5)  # Short delay for better UX

                # Final calculations
                if (weather_data.get("status") == "success" and
                        field_data.get("status") == "success" and
                        disease_data.get("status") == "success" and
                        crop_analysis.get("status") == "success"):

                    irrigation_plan = calculate_smart_irrigation(weather_data, field_data, disease_data, crop_analysis)

                    # Show results
                    st.success("Tahlil muvaffaqiyatli yakunlandi!")

                    # Create results container
                    st.markdown("<div class='result-box'>", unsafe_allow_html=True)

                    # Summary
                    st.subheader("📋 Sug'orish rejasi xulosasi")

                    # Show recommendations
                    if irrigation_plan.get("recommendations"):
                        st.markdown("##### 💡 AI tavsiyalari:")
                        for rec in irrigation_plan.get("recommendations"):
                            st.markdown(f"- {rec}")

                    # Show adjustment factors
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        temp_adj = irrigation_plan.get("temperature_adjustment", 0)
                        st.metric("Harorat ta'siri", f"{temp_adj * 100:+.0f}%")

                    with col2:
                        rain_adj = irrigation_plan.get("rain_adjustment", 0)
                        st.metric("Yomg'ir ta'siri", f"{rain_adj * 100:+.0f}%")

                    with col3:
                        disease_adj = irrigation_plan.get("disease_adjustment", 0)
                        st.metric("Kasallik ta'siri", f"{disease_adj * 100:+.0f}%")

                    with col4:
                        urgency_adj = irrigation_plan.get("soil_urgency_adjustment", 0)
                        st.metric("Tuproq namligi", f"{urgency_adj * 100:+.0f}%")

                    # Weather & Temperature summary
                    st.markdown("##### 🌡️ Ob-havo ma'lumotlari:")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("O'rtacha harorat", f"{weather_data.get('avg_temp', 0):.1f}°C")
                    with col2:
                        st.metric("Yomg'ir ehtimoli", f"{weather_data.get('avg_rain_prob', 0):.1f}%")

                    # Irrigation schedule table
                    st.markdown("##### 📅 Sug'orish jadvali:")

                    schedule_data = []
                    for item in irrigation_plan.get("schedule", []):
                        day_data = {
                            "№": item["irrigation_number"],
                            "Sana": item["date"].strftime("%d.%m.%Y"),
                            "Suv miqdori (m³)": f"{item['water_amount']:.2f}",
                            "Harorat (°C)": item.get("temperature", "N/A"),
                            "Yomg'ir ehtimoli (%)": item.get("rain_probability", "N/A")
                        }
                        schedule_data.append(day_data)

                    schedule_df = pd.DataFrame(schedule_data)
                    st.table(schedule_df)

                    # NEW: Add detailed water adjustment table
                    st.markdown("##### 💧 Suv hajmi o'zgarishi jadvali:")

                    detailed_data = []
                    for item in irrigation_plan.get("detailed_schedule", []):
                        # Format adjustments with +/- sign
                        temp_effect = item["temp_effect"]
                        rain_effect = item["rain_effect"]
                        disease_effect = item["disease_effect"]
                        soil_effect = item["soil_effect"]
                        total_effect = item["total_effect"]

                        detailed_row = {
                            "№": item["irrigation_number"],
                            "Sana": item["date"].strftime("%d.%m.%Y"),
                            "Bazaviy miqdor (m³)": f"{item['base_water']:.2f}",
                            "Harorat ta'siri (m³)": f"{temp_effect:+.2f}",
                            "Yomg'ir ta'siri (m³)": f"{rain_effect:+.2f}",
                            "Kasallik ta'siri (m³)": f"{disease_effect:+.2f}",
                            "Tuproq namligi ta'siri (m³)": f"{soil_effect:+.2f}",
                            "Jami o'zgarish (m³)": f"{total_effect:+.2f}",
                            "Yakuniy miqdor (m³)": f"{item['final_water']:.2f}"
                        }
                        detailed_data.append(detailed_row)

                    detailed_df = pd.DataFrame(detailed_data)
                    st.table(detailed_df)

                    # Highlight the changes in water amounts
                    st.markdown("""
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 10px;">
                    <small>
                    <span style="color: #4caf50;">🟢 Ijobiy qiymatlar</span> - suv miqdori oshganini bildiradi (ko'proq sug'orish zarur)<br>
                    <span style="color: #c62828;">🔴 Manfiy qiymatlar</span> - suv miqdori kamayganini bildiradi (kamroq sug'orish yetarli)<br>
                    </small>
                    </div>
                    """, unsafe_allow_html=True)

                    # Create a chart to visualize water amounts and factors
                    st.markdown("##### 📊 Sug'orish miqdori va o'zgarish omillari:")

                    # Prepare data for stacked bar chart
                    dates = [item["date"].strftime("%d.%m") for item in irrigation_plan.get("detailed_schedule", [])]
                    base_amounts = [item["base_water"] for item in irrigation_plan.get("detailed_schedule", [])]
                    temp_effects = [item["temp_effect"] for item in irrigation_plan.get("detailed_schedule", [])]
                    rain_effects = [item["rain_effect"] for item in irrigation_plan.get("detailed_schedule", [])]
                    disease_effects = [item["disease_effect"] for item in irrigation_plan.get("detailed_schedule", [])]
                    soil_effects = [item["soil_effect"] for item in irrigation_plan.get("detailed_schedule", [])]

                    # Create visualization showing impact of each factor
                    fig = go.Figure()

                    # Add base water amount
                    fig.add_trace(go.Bar(
                        name='Bazaviy suv miqdori',
                        x=dates,
                        y=base_amounts,
                        marker_color='rgba(55, 83, 109, 0.7)'
                    ))

                    # Add temperature effect
                    fig.add_trace(go.Bar(
                        name='Harorat ta\'siri',
                        x=dates,
                        y=temp_effects,
                        marker_color='rgba(219, 64, 82, 0.7)' if all(
                            t < 0 for t in temp_effects) else 'rgba(255, 144, 14, 0.7)'
                    ))

                    # Add rain effect
                    fig.add_trace(go.Bar(
                        name='Yomg\'ir ta\'siri',
                        x=dates,
                        y=rain_effects,
                        marker_color='rgba(50, 171, 96, 0.7)'
                    ))

                    # Add disease effect
                    fig.add_trace(go.Bar(
                        name='Kasallik ta\'siri',
                        x=dates,
                        y=disease_effects,
                        marker_color='rgba(128, 0, 128, 0.7)'
                    ))

                    # Add soil moisture effect
                    fig.add_trace(go.Bar(
                        name='Tuproq namligi ta\'siri',
                        x=dates,
                        y=soil_effects,
                        marker_color='rgba(0, 128, 128, 0.7)'
                    ))

                    # Add final line showing total water amount
                    final_amounts = [item["final_water"] for item in irrigation_plan.get("detailed_schedule", [])]
                    fig.add_trace(go.Scatter(
                        name='Yakuniy suv miqdori',
                        x=dates,
                        y=final_amounts,
                        mode='lines+markers',
                        line=dict(color='rgba(0, 0, 0, 0.7)', width=2),
                        marker=dict(size=8)
                    ))

                    # Update layout
                    fig.update_layout(
                        title='Sug\'orish miqdori va unga ta\'sir qiluvchi omillar',
                        xaxis_title='Sana',
                        yaxis_title='Suv miqdori (m³)',
                        barmode='relative',
                        hovermode="x unified",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Weather forecast visualization
                    st.markdown("##### 🌦️ Ob-havo bashorati:")

                    # Create dual-axis chart for temperature and rain probability
                    fig2 = go.Figure()

                    # Add temperature trace
                    fig2.add_trace(go.Scatter(
                        x=weather_data.get("dates", []),
                        y=weather_data.get("temps", []),
                        name="Harorat (°C)",
                        mode="lines+markers",
                        line=dict(color="#FF9800", width=2),
                        marker=dict(size=8),
                    ))

                    # Add rain probability trace
                    fig2.add_trace(go.Bar(
                        x=weather_data.get("dates", []),
                        y=weather_data.get("rain_probs", []),
                        name="Yomg'ir ehtimoli (%)",
                        marker_color="rgba(0, 120, 212, 0.6)",
                        yaxis="y2"
                    ))

                    # Update layout for dual-axis chart
                    fig2.update_layout(
                        title="Keyingi kunlar uchun ob-havo bashorati",
                        xaxis_title="Sana",
                        yaxis=dict(
                            title="Harorat (°C)",
                            titlefont=dict(color="#FF9800"),
                            tickfont=dict(color="#FF9800")
                        ),
                        yaxis2=dict(
                            title="Yomg'ir ehtimoli (%)",
                            titlefont=dict(color="#0078D4"),
                            tickfont=dict(color="#0078D4"),
                            anchor="x",
                            overlaying="y",
                            side="right",
                            range=[0, 100]
                        ),
                        hovermode="x unified",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )

                    st.plotly_chart(fig2, use_container_width=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                else:
                    st.error("Ma'lumotlarni tahlil qilishda xatolik yuz berdi.")

                    if weather_data.get("status") == "error":
                        st.warning(f"Ob-havo ma'lumotlari xatosi: {weather_data.get('message')}")

                    if field_data.get("status") == "error":
                        st.warning(f"Maydon ma'lumotlari xatosi: {field_data.get('message')}")

                    if disease_data.get("status") == "error":
                        st.warning(f"Kasallik ma'lumotlari xatosi: {disease_data.get('message')}")

                    if crop_analysis.get("status") == "error":
                        st.warning(f"Ekin ma'lumotlari xatosi: {crop_analysis.get('message')}")

    with tab2:
        st.subheader("Qo'shimcha ma'lumotlar")

        st.markdown("""
        Ushbu sahifada ekinlaringiz haqidagi qo'shimcha ma'lumotlar va tavsiyalar beriladi.

        ### 📊 Ma'lumotlar manbai

        **Aqlli Sug'orish AI** quyidagi ma'lumotlar asosida tahlil qiladi:

        1. **Ob-havo ma'lumotlari:** 
           - Viloyat bo'yicha 1 oylik o'rtacha harorat
           - Yog'ingarchilik ehtimoli

        2. **Maydon ma'lumotlari:**
           - Ekin turi
           - Oxirgi sug'orilgan sana
           - Tuproq namligi

        3. **Kasallik ma'lumotlari:**
           - Kasallik turi
           - Kasallikka qarshi davolash usullari

        4. **Ekin ma'lumotlari:**
           - O'sish bosqichi
           - Yer maydoni
           - Sug'orish me'yorlari
        """)

        # Collapsible sections for additional info
        with st.expander("ℹ️ Ekinlar va ularning sug'orish me'yorlari"):
            st.markdown("""
            **Bug'doy:**
            - Unib chiqish: 4-5 mm/kun (7-10 kun)
            - Tuplanish: 5-7 mm/kun (30-40 kun)
            - Poya cho'zilishi: 7-8 mm/kun (20-30 kun)
            - Gullash: 8-10 mm/kun (10-15 kun)
            - Don to'lishi: 6-8 mm/kun (15-20 kun)
            - Pishish: 3-4 mm/kun (10-15 kun)

            **Paxta:**
            - Unib chiqish: 4-5 mm/kun (7-10 kun)
            - O'sish davri: 6-8 mm/kun (30-40 kun)
            - Gullash: 8-10 mm/kun (20-30 kun)
            - Ko'sak hosil qilish: 7-9 mm/kun (30-40 kun)
            - Pishish: 5-6 mm/kun (15-20 kun)
            """)

        with st.expander("🌧️ Yomg'ir ta'sirida sug'orish miqdorini hisoblash"):
            st.markdown("""
            **Yomg'ir ehtimoli ta'siri:**

            - 0-20% — Sug'orish miqdoriga ta'sir etmaydi
            - 21-40% — Sug'orish miqdori 10% kamaytiriladi
            - 41-60% — Sug'orish miqdori 20% kamaytiriladi
            - 61-80% — Sug'orish miqdori 30% kamaytiriladi
            - 81-100% — Sug'orish miqdori 40% kamaytiriladi

            **Misol:** Agar 5 m³ sug'orish rejalashtirilgan bo'lsa va yomg'ir ehtimoli 70% bo'lsa, sug'orish miqdori 5 × (1 - 0.3) = 3.5 m³ ga kamaytiriladi.
            """)

        with st.expander("🌡️ Harorat ta'sirida sug'orish miqdorini hisoblash"):
            st.markdown("""
            **Harorat ta'siri:**

            - < 15°C — Sug'orish miqdori 10% kamaytiriladi
            - 15-25°C — Sug'orish miqdoriga ta'sir etmaydi
            - 25-30°C — Sug'orish miqdori 10% oshiriladi
            - > 30°C — Sug'orish miqdori 20% oshiriladi

            **Misol:** Agar 5 m³ sug'orish rejalashtirilgan bo'lsa va harorat 32°C bo'lsa, sug'orish miqdori 5 × (1 + 0.2) = 6 m³ ga oshiriladi.
            """)

        with st.expander("🦠 Kasalliklar ta'sirida sug'orish miqdorini hisoblash"):
            st.markdown("""
            **Kasalliklar ta'siri:**

            - **Fitoftoroz** — Sug'orish miqdori 30% kamaytiriladi, barglarni ho'llamasdan
            - **Bakterial chirish** — Sug'orish miqdori 30-40% kamaytiriladi
            - **Un shudring** — Sug'orish miqdori 20% kamaytiriladi
            - **Fuzarioz** — Sug'orish miqdori 30% kamaytiriladi

            **Muhim eslatma:** Kasallik aniqlanganda, sug'orishni kamaytirishdan tashqari, tegishli kimyoviy ishlov berish ham tavsiya etiladi.
            """)

    with tab3:
        st.subheader("Yordam")

        st.markdown("""
        ### Qanday qilib Aqlli Sug'orish AI dan foydalanish mumkin?

        1. **Viloyat tanlash** — Ob-havo ma'lumotlari olinadigan hududni tanlang
        2. **Maydon tanlash** — Tahlil qilinadigan maydonni tanlang
        3. **O'sish bosqichini tanlash** — Ekinning hozirgi o'sish bosqichini tanlang
        4. **Maydon o'lchamini kiriting** — Sug'orish miqdorini hisoblash uchun maydon o'lchamini kiriting
        5. **Kasallik mavjudligini belgilang** — Agar ekinlarda kasallik bo'lsa, mos variantni tanlang
        6. **Tahlil qilish** tugmasini bosing — AI barcha ma'lumotlarni tahlil qilib, optimal sug'orish jadvalini taqdim etadi

        ### Natijalarni tushunish

        **Sug'orish jadvali:**
        - Jadvalda keyingi 5 ta sug'orish vaqti va miqdori ko'rsatiladi
        - Har bir sana uchun suv miqdori ob-havo, tuproq namligi, ekin turi va kasallik holatiga qarab moslashtiriladi

        **Suv hajmi o'zgarishi jadvali:**
        - Bu jadvalda har bir omilning sug'orish miqdoriga ta'siri ko'rsatiladi
        - Bazaviy miqdor - hech qanday ta'sirsiz normal sug'orish miqdori
        - Harorat, yomg'ir, kasallik va tuproq namligi ta'sirlari alohida ko'rsatiladi
        - Ijobiy qiymatlar (+) suv miqdori oshganini, manfiy qiymatlar (-) kamayganini bildiradi
        - Yakuniy miqdor - barcha omillar hisobga olingan holda tavsiya etilgan sug'orish miqdori

        **Tavsiyalar:**
        - AI tomonidan berilgan tavsiyalar ekinlaringizni samarali parvarish qilishga yordam beradi
        - Tavsiyalarga rioya qilish suv resurslarini tejash va hosilni oshirishga yordam beradi

        **Muammolar yechimi:**
        - Agar ma'lumotlar olinmasa, maydonlar va ekinlar to'g'ri tanlangan-tanlanmaganini tekshiring
        - Xatolik yuzaga kelsa, ma'lumotlarni qayta kiritib ko'ring
        """)


def register_page():
    """Register the AI page in the Streamlit app"""
    return show_ai_results
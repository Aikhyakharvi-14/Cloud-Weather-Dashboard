
import streamlit as st
import firebase_admin

from pathlib import Path
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter


# ==========================================
# 1. FIREBASE CONNECTION
# ==========================================

@st.cache_resource
def connect_firebase():

    key_path = (
        Path(__file__).resolve().parent
        / "firebase-service-account.json"
    )

    # LOCAL CONNECTION: use downloaded JSON file
    if key_path.is_file():

        firebase_credential = credentials.Certificate(
            str(key_path)
        )

    # CLOUD CONNECTION: use Streamlit secrets
    elif "firebase_service_account" in st.secrets:

        service_account_info = dict(
            st.secrets["firebase_service_account"]
        )

        firebase_credential = credentials.Certificate(
            service_account_info
        )

    else:

        raise RuntimeError(
            "Firebase credentials not found. "
            "Check your local JSON file or Streamlit secrets."
        )

    # Initialize Firebase only once
    try:
        firebase_app = firebase_admin.get_app()

    except ValueError:
        firebase_app = firebase_admin.initialize_app(
            firebase_credential
        )

    # Connect to Firestore
    database = firestore.client(app=firebase_app)

    return database


# ==========================================
# 2. SAVE WEATHER DATA
# ==========================================

def save_weather_data(current, forecast_df):

    db = connect_firebase()

    city = current["name"]
    main = current["main"]
    weather = current["weather"][0]
    wind = current["wind"]

    forecast_records = []

    for _, row in forecast_df.iterrows():

        forecast_records.append({

            "date": row["Date"].isoformat(),

            "temperature": float(
                row["Temperature"]
            ),

            "humidity": int(
                row["Humidity"]
            ),

            "wind_speed_kmh": float(
                row["Wind Speed"]
            ),

            "rainfall": float(
                row["Rainfall"]
            ),

            "weather": str(
                row["Weather"]
            )
        })

    record = {

        "city": city,

        "country": current["sys"]["country"],

        "temperature": float(main["temp"]),

        "feels_like": float(main["feels_like"]),

        "minimum_temperature": float(main["temp_min"]),

        "maximum_temperature": float(main["temp_max"]),

        "humidity": int(main["humidity"]),

        "pressure": int(main["pressure"]),

        "wind_speed_kmh": float(wind["speed"] * 3.6),

        "visibility_m": int(current.get("visibility", 0)),

        "weather": weather["description"],

        "weather_icon": weather["icon"],

        "forecast": forecast_records,

        "weather_api_timestamp": int(current["dt"]),

        "saved_at": firestore.SERVER_TIMESTAMP
    }

    # Create a new Firestore document
    db.collection("weather_history").add(record)

    return True


# ==========================================
# 3. RETRIEVE WEATHER HISTORY
# ==========================================


def get_weather_history(city, limit=20):
    db = connect_firebase()

    documents = (
        db.collection("weather_history")
        .where("city", "==", city)
        .stream()
    )

    records = []

    for document in documents:
        data = document.to_dict()
        data["record_id"] = document.id
        records.append(data)

    # Sort records by saved_at, newest first
    records.sort(
        key=lambda item: item.get("saved_at") or datetime.min,
        reverse=True
    )

    # Display only the latest records
    records = records[:limit]

    for data in records:
        saved_at = data.get("saved_at")

        if saved_at:
            data["saved_at"] = saved_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

    return records

# ==========================================
# 4. TEST FIREBASE CONNECTION
# ==========================================

def test_firebase_connection():

    db = connect_firebase()

    # A harmless read operation to verify access
    list(
        db.collection("weather_history")
        .limit(1)
        .stream()
    )

    return True

import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
import folium
from folium.plugins import MarkerCluster, AntPath
from folium import CustomIcon, IFrame
from streamlit_folium import st_folium
import pandas as pd
import geopy.distance
import sqlite3
import hashlib
from sklearn.ensemble import RandomForestClassifier
import joblib

st.text("고혈압 정보를 확인할 수 있습니다")
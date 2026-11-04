"""Home: does anything need me today? One laptop screen, no scrolling. Plan: dashboard/PLAN.md, screen 1.

It shows what the routines wrote and compares nothing, so it raises nothing new.
"""

import streamlit as st

import data
import view

st.html(view.HOME_CSS)
st.html(view.home(data.home_view(), data.now_utc()))

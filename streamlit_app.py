"""
Entry point for Streamlit Cloud deployment.
Forwards execution directly to app.py.
"""
import runpy

runpy.run_path("app.py")

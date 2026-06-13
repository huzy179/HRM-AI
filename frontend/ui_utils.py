from __future__ import annotations
import streamlit as st

def apply_premium_style() -> None:
    """
    Applies custom CSS to Streamlit pages to create a stunning, premium UI/UX.
    Uses Outfit/Inter font, custom glassmorphism containers, smooth animations, and curated colors.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        
        /* Apply fonts */
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Title and Header customization */
        h1 {
            font-family: 'Outfit', sans-serif;
            background: linear-gradient(135deg, #FF6B6B 0%, #4D96FF 50%, #6BCB77 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin-bottom: 0.5rem;
        }
        
        h2, h3, h4 {
            font-family: 'Outfit', sans-serif;
            color: #E2E8F0;
            font-weight: 600;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #0F172A !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }

        /* Button customization */
        div.stButton > button {
            background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 1.2rem !important;
            font-weight: 500 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        }
        div.stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3), 0 4px 6px -2px rgba(59, 130, 246, 0.05) !important;
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        }
        div.stButton > button:active {
            transform: translateY(0px) !important;
        }

        /* Input styling */
        div.stTextInput > div > div > input,
        div.stNumberInput > div > div > input,
        div.stSelectbox > div > div > select {
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background-color: #1E293B !important;
            color: #F8FAFC !important;
            transition: border-color 0.2s ease-in-out !important;
        }
        div.stTextInput > div > div > input:focus {
            border-color: #3B82F6 !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
        }

        /* Cards and Expander Styling */
        div[data-testid="stExpander"] {
            background: rgba(30, 41, 59, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
            backdrop-filter: blur(8px);
        }
        
        /* Metric widget styling */
        div[data-testid="stMetricValue"] {
            font-size: 2.2rem !important;
            font-weight: 700 !important;
            color: #3B82F6 !important;
            font-family: 'Outfit', sans-serif;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #94A3B8 !important;
        }
        div[data-testid="stMetric"] {
            background: rgba(30, 41, 59, 0.6) !important;
            padding: 1rem !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
        }

        /* Custom success/info/error styles */
        div.stAlert {
            border-radius: 12px !important;
            border: none !important;
            background-color: rgba(30, 41, 59, 0.8) !important;
            border-left: 4px solid #3B82F6 !important;
        }
        div.stAlert[data-baseweb="notification"] {
            background-color: rgba(30, 41, 59, 0.8) !important;
        }

        /* Custom Chat bubble styles */
        .chat-bubble-user {
            background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
            color: white;
            padding: 12px 16px;
            border-radius: 16px 16px 4px 16px;
            margin-bottom: 12px;
            max-width: 80%;
            align-self: flex-end;
            margin-left: auto;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.15);
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .chat-bubble-agent {
            background: rgba(30, 41, 59, 0.85);
            color: #F1F5F9;
            padding: 16px 20px;
            border-radius: 16px 16px 16px 4px;
            margin-bottom: 12px;
            max-width: 85%;
            align-self: flex-start;
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .citation-card {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 8px;
            padding: 10px 14px;
            margin-top: 8px;
            font-size: 0.85rem;
            color: #94A3B8;
        }
        
        .citation-tag {
            display: inline-block;
            background: rgba(59, 130, 246, 0.15);
            color: #60A5FA;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            margin-bottom: 6px;
            font-size: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

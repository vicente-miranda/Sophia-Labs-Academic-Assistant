# Proprietary License
# Effective Date: 3rd of January of 2025
#
# Copyright (c) 2025 Sophia Labs
#
# This software is the proprietary property of Sophia Labs and is provided exclusively for 
# evaluation purposes by Tiago Santos or NOVA IMS staff. Any other use, reproduction, 
# distribution, or modification without explicit written permission from the authors 
# is strictly prohibited.
#
# Consult the license for detailed terms and conditions before using this software.

import streamlit as st
from menu import menu
from PIL import Image
import os
import json
from streamlit_lottie import st_lottie

def home_page():
    # Set page configuration as the very first Streamlit command
    st.set_page_config(page_title="Home", layout="wide")
    
    # Redirect if needed
    menu()
    
    # Inject custom CSS styles
    st.markdown("""
        <style>
        /* Custom styles for the Home page */
        body {
            background-color: #121212;
            color: #e8e8e8;
        }
        .static-title {
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            color: #ff8c00; /* Orange for strong contrast */
            margin-bottom: 0;
        }
        .sub-title {
            font-size: 20px;
            color: #e0e0e0; /* Light gray for better contrast */
            text-align: center;
            margin-top: 0;
            margin-bottom: 2rem;
        }
        .separator {
            border: 0;
            height: 2px;
            background: linear-gradient(to right, #004d99, #ffffff, #004d99); /* High-contrast gradient */
            margin: 20px auto;
            width: 80%;
        }
        .highlight {
            color: #00aaff;
            font-weight: bold;
        }
        .section-title {
            font-size: 32px;
            font-weight: bold;
            color: #00aaff; /* Bright blue for visibility */
            margin-bottom: 20px;
            text-align: center;
        }
        .feature-card {
            border: 1px solid #333333;
            border-radius: 8px;
            padding: 20px;
            margin: 10px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.5);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            background-color: #1e1e1e; /* Darker background for contrast */
            text-align: center;
        }
        .feature-card:hover {
            transform: scale(1.05);
            box-shadow: 3px 3px 15px rgba(0, 0, 0, 0.8);
        }
        .feature-card h3 {
            font-size: 24px;
            color: #00aaff;
            margin-bottom: 10px;
        }
        .feature-card p {
            font-size: 16px;
            color: #cccccc; /* Light gray for text */
        }
        .testimonial {
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 8px;
            margin: 10px 0;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.5);
            text-align: center;
        }
        .testimonial p {
            font-size: 16px;
            color: #e0e0e0;
            font-style: italic;
        }
        .testimonial strong {
            color: #ff8c00;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Page Title
    st.markdown("<div class='static-title'>Welcome to Sophia Labs</div>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Your intelligent chatbot platform for seamless and efficient communication.</p>", unsafe_allow_html=True)
    
    # Welcome Message
    st.markdown("""
        <div style="max-width: 900px; margin: auto; text-align: center; padding: 2rem;">
            <p>
                At <span class="highlight">Sophia Labs</span>, we revolutionize education with AI-driven solutions 
                designed to simplify learning, enhance productivity, and streamline communication.
            </p>
            <p>
                Our platform empowers students, educators, and administrators to connect and collaborate like never before.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Visual Separator
    st.markdown("<hr class='separator'>", unsafe_allow_html=True)
    
    # Feature Section
    st.markdown("<div class='section-title'>Why Choose Sophia Labs?</div>", unsafe_allow_html=True)
    feature_cols = st.columns(3)
    
    features = [
        {
            "title": "Intelligent Chatbots",
            "description": "AI-powered chatbots tailored to your academic needs, providing instant and accurate responses.",
            "icon": "🤖"  # Emoji as a placeholder for an icon
        },
        {
            "title": "Enhanced Productivity",
            "description": "Streamline your tasks and focus on what matters most with our innovative features.",
            "icon": "⚡"
        },
        {
            "title": "Seamless Integration",
            "description": "Easily connect our tools with existing systems for a smooth and unified experience.",
            "icon": "🔗"
        }
    ]
    
    for idx, feature in enumerate(features):
        with feature_cols[idx]:
            st.markdown(f"""
                <div class="feature-card">
                    <h3>{feature['icon']} {feature['title']}</h3>
                    <p>{feature['description']}</p>
                </div>
            """, unsafe_allow_html=True)
    
    # Visual Separator
    st.markdown("<hr class='separator'>", unsafe_allow_html=True)
    
    # Testimonials Section
    st.markdown("<div class='section-title'>What Our Users Say</div>", unsafe_allow_html=True)
    testimonial_container = st.container()
    with testimonial_container:
        testimonial1, testimonial2 = st.columns(2)
        
        with testimonial1:
            st.markdown("""
                <div class="testimonial">
                    <p>
                        <strong>John Doe, Student:</strong> "Sophia Labs has completely transformed how I study and interact with my professors. Highly recommend!"
                    </p>
                </div>
            """, unsafe_allow_html=True)
        
        with testimonial2:
            st.markdown("""
                <div class="testimonial">
                    <p>
                        <strong>Jane Smith, Educator:</strong> "An invaluable tool for managing my courses and connecting with students effectively."
                    </p>
                </div>
            """, unsafe_allow_html=True)
    
    # Final Touch
    st.markdown("""
        <div style="max-width: 900px; margin: auto; text-align: center; padding: 2rem;">
            <p style="font-size: 18px; color: #e0e0e0;">
                <em>"Explore. Engage. Excel."</em> – Your success is our mission.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
        <div style="text-align: center; font-size: 12px; color: #e0e0e0; margin-top: 2rem;">
            © 2025 Sophia Labs. All rights reserved.
        </div>
    """, unsafe_allow_html=True)

# To run the Home page independently
if __name__ == "__main__":
    home_page()

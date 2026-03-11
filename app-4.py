import streamlit as st
import requests
import json
import os
import time
from datetime import datetime
import base64
from pathlib import Path
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from agents.idea_generator import IdeaGenerator
from agents.script_writer import ScriptWriter
from agents.video_producer import VideoProducer

# Page configuration
st.set_page_config(
    page_title="Autonomous AI Agent Studio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-top: 1.5rem;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #4CAF50;
    }
    .video-container {
        display: flex;
        justify-content: center;
        margin-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
    }
    .agent-status {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class AutonomousAgentApp:
    def __init__(self):
        self.config = Config()
        self.idea_generator = IdeaGenerator()
        self.script_writer = ScriptWriter()
        self.video_producer = VideoProducer()

        # Create directories
        Path(self.config.VIDEO_OUTPUT_DIR).mkdir(exist_ok=True)
        Path(self.config.ASSETS_DIR).mkdir(exist_ok=True)

    def get_available_avatars(self):
        """Fetch available avatars from HeyGen API"""
        try:
            headers = {
                "X-Api-Key": self.config.HEYGEN_API_KEY,
                "Content-Type": "application/json"
            }

            response = requests.get(
                "https://api.heygen.com/v1/avatars",
                headers=headers
            )

            if response.status_code == 200:
                avatars = response.json().get("data", {}).get("avatars", [])
                return {avatar["name"]: avatar["avatar_id"] for avatar in avatars}
            else:
                # Fallback to default avatars if API fails
                return {
                    "Adam": "9e5c5445d1c84e1d8e2f8c5c5c5c5c5c",
                    "Emma": "8d7c5445d1c84e1d8e2f8c5c5c5c5c5d",
                    "Alex": "7c6c5445d1c84e1d8e2f8c5c5c5c5c5e",
                    "Sophia": "6b5c5445d1c84e1d8e2f8c5c5c5c5c5f",
                    "Michael": "5a4c5445d1c84e1d8e2f8c5c5c5c5c5g"
                }
        except Exception as e:
            st.error(f"Error fetching avatars: {e}")
            return {}

    def get_available_voices(self):
        """Available voices for HeyGen"""
        return {
            "Adam (US)": "1bd001e7e50f421d891986aad5158bc8",
            "Emma (US)": "2ce112f7e60f531e992097bbe6269cd9",
            "Alex (UK)": "3df22307f70f642fa8a1a88cc7378dea",
            "Sophia (AU)": "4ef33417f80f753fbb2b299dd8489efb",
            "Michael (US)": "5ff44527f90f864fcc3c3aaee959a00c"
        }

    def generate_video(self, script, avatar_id, voice_id, video_title):
        """Generate video using HeyGen API v2"""
        try:
            headers = {
                "X-Api-Key": self.config.HEYGEN_API_KEY,
                "Content-Type": "application/json"
            }

            payload = {
                "video_inputs": [{
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script,
                        "voice_id": voice_id
                    },
                    "background": {
                        "type": "color",
                        "value": "#FFFFFF"
                    }
                }],
                "dimension": {
                    "width": 1920,
                    "height": 1080
                },
                "test": False
            }

            st.info("🚀 Generating video... This may take 1-2 minutes.")

            # Make API request
            response = requests.post(
                self.config.HEYGEN_API_URL,
                headers=headers,
                json=payload
            )
</div>
import streamlit as st
import requests
import json
import os
import time
from datetime import datetime
import base64
from pathlib import Path
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from agents.idea_generator import IdeaGenerator
from agents.script_writer import ScriptWriter
from agents.video_producer import VideoProducer

# Page configuration
st.set_page_config(
    page_title="Autonomous AI Agent Studio",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-top: 1.5rem;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #4CAF50;
    }
    .video-container {
        display: flex;
        justify-content: center;
        margin-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
    }
    .agent-status {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class AutonomousAgentApp:
    def __init__(self):
        self.config = Config()
        self.idea_generator = IdeaGenerator()
        self.script_writer = ScriptWriter()
        self.video_producer = VideoProducer()

        # Create directories
        Path(self.config.VIDEO_OUTPUT_DIR).mkdir(exist_ok=True)
        Path(self.config.ASSETS_DIR).mkdir(exist_ok=True)

    def get_available_avatars(self):
        """Fetch available avatars from HeyGen API"""
        try:
            headers = {
                "X-Api-Key": self.config.HEYGEN_API_KEY,
                "Content-Type": "application/json"
            }

            response = requests.get(
                "https://api.heygen.com/v1/avatars",
                headers=headers
            )

            if response.status_code == 200:
                avatars = response.json().get("data", {}).get("avatars", [])
                return {avatar["name"]: avatar["avatar_id"] for avatar in avatars}
            else:
                # Fallback to default avatars if API fails
                return {
                    "Adam": "9e5c5445d1c84e1d8e2f8c5c5c5c5c5c",
                    "Emma": "8d7c5445d1c84e1d8e2f8c5c5c5c5c5d",
                    "Alex": "7c6c5445d1c84e1d8e2f8c5c5c5c5c5e",
                    "Sophia": "6b5c5445d1c84e1d8e2f8c5c5c5c5c5f",
                    "Michael": "5a4c5445d1c84e1d8e2f8c5c5c5c5c5g"
                }
        except Exception as e:
            st.error(f"Error fetching avatars: {e}")
            return {}

    def get_available_voices(self):
        """Available voices for HeyGen"""
        return {
            "Adam (US)": "1bd001e7e50f421d891986aad5158bc8",
            "Emma (US)": "2ce112f7e60f531e992097bbe6269cd9",
            "Alex (UK)": "3df22307f70f642fa8a1a88cc7378dea",
            "Sophia (AU)": "4ef33417f80f753fbb2b299dd8489efb",
            "Michael (US)": "5ff44527f90f864fcc3c3aaee959a00c"
        }

    def generate_video(self, script, avatar_id, voice_id, video_title):
        """Generate video using HeyGen API v2"""
        try:
            headers = {
                "X-Api-Key": self.config.HEYGEN_API_KEY,
                "Content-Type": "application/json"
            }

            payload = {
                "video_inputs": [{
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script,
                        "voice_id": voice_id
                    },
                    "background": {
                        "type": "color",
                        "value": "#FFFFFF"
                    }
                }],
                "dimension": {
                    "width": 1920,
                    "height": 1080
                },
                "test": False
            }

            st.info("🚀 Generating video... This may take 1-2 minutes.")

            # Make API request
            response = requests.post(
                self.config.HEYGEN_API_URL,
                headers=headers,
                json=payload
            )
</div>

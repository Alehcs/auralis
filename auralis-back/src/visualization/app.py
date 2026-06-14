"""Legacy Streamlit interface for inspecting magnetograms and model output.

The FastAPI/React app is the maintained demo surface. This file remains useful
for local experiments with uploaded FITS files, but it should not be treated as
the reference serving path for the promoted ONNX model.
"""

import os
import sys
from pathlib import Path
import warnings

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from astropy.io import fits
from PIL import Image
import torch
import torch.nn as nn

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="AURALIS - Solar Analysis",
    page_icon="☉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stContainer {
        border-radius: 10px;
        padding: 20px;
        background-color: rgba(28, 131, 225, 0.05);
        border: 1px solid rgba(28, 131, 225, 0.1);
        margin-bottom: 20px;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1 {
        font-weight: 600;
        letter-spacing: -0.5px;
    }

    h3 {
        font-weight: 500;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: #E0E0E0;
    }

    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }

    .info-card {
        background: linear-gradient(135deg, rgba(28, 131, 225, 0.1) 0%, rgba(28, 131, 225, 0.05) 100%);
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid rgba(28, 131, 225, 0.2);
        height: 100%;
    }

    .info-card h4 {
        margin-top: 0;
        font-size: 1.1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "coronium_v3_final.pth"
DATA_PATH = PROJECT_ROOT / "data" / "processed"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# ============================================================================
# MODEL ARCHITECTURE
# ============================================================================
class Coronium(nn.Module):
    """Legacy single-channel Coronium architecture used by the Streamlit demo."""

    def __init__(self, dropout_rate: float = 0.3):
        super(Coronium, self).__init__()

        # Conv block 1: (1, 512, 512) -> (32, 256, 256)
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout1 = nn.Dropout2d(p=dropout_rate)

        # Conv block 2: (32, 256, 256) -> (64, 128, 128)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout2 = nn.Dropout2d(p=dropout_rate)

        # Conv block 3: (64, 128, 128) -> (128, 64, 64)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout3 = nn.Dropout2d(p=dropout_rate)

        # Conv block 4: (128, 64, 64) -> (256, 32, 32)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout4 = nn.Dropout2d(p=dropout_rate)

        # Global pooling and regression
        self.global_avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(256, 1)
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.pool1(x)
        x = self.dropout1(x)

        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu(x)
        x = self.pool2(x)
        x = self.dropout2(x)

        x = self.conv3(x)
        x = self.bn3(x)
        x = self.relu(x)
        x = self.pool3(x)
        x = self.dropout3(x)

        x = self.conv4(x)
        x = self.bn4(x)
        x = self.relu(x)
        x = self.pool4(x)
        x = self.dropout4(x)

        x = self.global_avg_pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


# ============================================================================
# DATA LOADING AND PROCESSING
# ============================================================================

@st.cache_resource
def load_model():
    """Load the legacy Streamlit checkpoint once per Streamlit process."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = Coronium(dropout_rate=0.3)

    if MODEL_PATH.exists():
        checkpoint = torch.load(MODEL_PATH, map_location=device)
        model.load_state_dict(checkpoint)
        model.eval()
    else:
        st.error(f"Model not found: {MODEL_PATH}")
        st.stop()

    return model, device


@st.cache_data
def load_available_images():
    """Return processed magnetogram filenames for the sidebar selector."""
    if not DATA_PATH.exists():
        return []
    npy_files = sorted(list(DATA_PATH.glob("*.npy")))
    return [f.name for f in npy_files]


def process_fits_file(fits_file):
    """Convert an uploaded FITS file into the legacy single-channel input.

    Streamlit upload objects are written to a temporary FITS path because the
    astropy reader expects a file-like source with FITS semantics.
    """
    try:
        with open("/tmp/temp_magnetogram.fits", "wb") as f:
            f.write(fits_file.getbuffer())

        with fits.open("/tmp/temp_magnetogram.fits") as hdul:
            data = hdul[1].data

        from PIL import Image as PILImage
        img = PILImage.fromarray(data.astype(np.float32))
        img_resized = img.resize((512, 512), PILImage.LANCZOS)
        img_array = np.array(img_resized)

        # Normalize to [-1, 1]
        img_min = np.min(img_array)
        img_max = np.max(img_array)
        if img_max > img_min:
            img_normalized = 2 * (img_array - img_min) / (img_max - img_min) - 1
        else:
            img_normalized = np.zeros_like(img_array)

        return img_normalized
    except Exception as e:
        st.error(f"FITS processing error: {e}")
        return None


def predict_activity(model, device, image_array):
    """Run deterministic inference on a preprocessed legacy magnetogram."""
    img_tensor = torch.from_numpy(image_array).float().unsqueeze(0).unsqueeze(0)
    img_tensor = img_tensor.to(device)

    with torch.no_grad():
        prediction = model(img_tensor)

    return float(prediction.cpu().numpy()[0, 0])


def create_gauge_chart(value):
    """Build the legacy activity gauge used by the Streamlit page."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Activity Index", 'font': {'size': 18, 'color': '#E0E0E0'}},
        number={'font': {'size': 42, 'color': '#FFFFFF', 'weight': 700}},
        gauge={
            'axis': {
                'range': [None, 300],
                'tickwidth': 2,
                'tickcolor': "rgba(255,255,255,0.4)",
                'tickfont': {'size': 12, 'color': '#A0A0A0'}
            },
            'bar': {'color': "#1E88E5", 'thickness': 0.7},
            'bgcolor': "rgba(0,0,0,0.3)",
            'borderwidth': 2,
            'bordercolor': "rgba(255,255,255,0.2)",
            'steps': [
                {'range': [0, 100], 'color': 'rgba(46, 204, 113, 0.3)'},
                {'range': [100, 200], 'color': 'rgba(243, 156, 18, 0.3)'},
                {'range': [200, 300], 'color': 'rgba(231, 76, 60, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "#FFFFFF", 'width': 3},
                'thickness': 0.8,
                'value': value
            }
        }
    ))

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#E0E0E0", 'family': "Arial"},
        height=320,
        margin=dict(l=30, r=30, t=60, b=30)
    )

    return fig


def get_risk_level(activity_index):
    """Map the legacy activity index to coarse UI activity bands."""
    if activity_index < 100:
        return "LOW", "#2ECC71", "Normal solar activity"
    elif activity_index < 200:
        return "MODERATE", "#F39C12", "Moderate solar activity"
    else:
        return "HIGH", "#E74C3C", "High solar activity"


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Render the legacy Streamlit dashboard."""

    # Header
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0 0.5rem 0;'>
        <h1 style='margin: 0; font-size: 2.8rem; font-weight: 600; color: #FFFFFF;'>
            AURALIS
        </h1>
        <p style='margin: 0.3rem 0 0 0; font-size: 0.95rem; color: #A0A0A0; font-weight: 400;'>
            Local Dataset Analysis | Model: <span style='color: #1E88E5;'>Coronium V3 PRO</span> | Val MAE: <span style='color: #2ECC71;'>5.52%</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # Load model
    model, device = load_model()

    # Sidebar
    st.sidebar.markdown("### Data Source")

    data_source = st.sidebar.radio(
        "Select data origin:",
        ["Processed Images", "Upload FITS"],
        index=0,
        label_visibility="collapsed"
    )

    image_array = None
    image_name = None

    if data_source == "Processed Images":
        available_images = load_available_images()

        if not available_images:
            st.sidebar.error("No images available")
            st.stop()

        st.sidebar.caption(f"{len(available_images)} magnetograms available")

        selected_image = st.sidebar.selectbox(
            "Select magnetogram:",
            available_images,
            index=0
        )

        if selected_image:
            image_path = DATA_PATH / selected_image
            image_array = np.load(image_path)
            image_name = selected_image

    else:
        uploaded_file = st.sidebar.file_uploader(
            "Upload FITS file",
            type=["fits", "fit"]
        )

        if uploaded_file is not None:
            with st.spinner("Processing FITS file..."):
                image_array = process_fits_file(uploaded_file)
                image_name = uploaded_file.name

    st.sidebar.write("")
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style='text-align: center; font-size: 0.85rem; color: #808080;'>
        <p>Deep learning-based solar<br>activity analysis system</p>
    </div>
    """, unsafe_allow_html=True)

    # Main visualization
    if image_array is not None:
        # Execute prediction
        with st.spinner("Analyzing solar activity..."):
            activity_index = predict_activity(model, device, image_array)

        risk_level, risk_color, risk_desc = get_risk_level(activity_index)

        # Analysis container
        with st.container():
            st.markdown("### Magnetogram Analysis")

            col_image, col_gauge = st.columns([2, 1], gap="large")

            with col_image:
                # Scientific visualization with RdBu_r colormap
                fig_mag, ax = plt.subplots(figsize=(10, 10), facecolor='#0E1117')
                ax.set_facecolor('#0E1117')

                im = ax.imshow(
                    image_array,
                    cmap='RdBu_r',
                    origin='lower',
                    vmin=-1,
                    vmax=1
                )

                ax.axis('off')
                ax.set_title(
                    image_name,
                    color='white',
                    fontsize=13,
                    pad=15,
                    fontweight='normal'
                )

                cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                cbar.set_label('Magnetic Flux [Gauss]', color='white', fontsize=11)
                cbar.ax.yaxis.set_tick_params(color='white', labelsize=9)
                plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

                st.pyplot(fig_mag, width='stretch')
                plt.close()

                st.caption("Red: positive polarity | Blue: negative polarity | White: neutral")

            with col_gauge:
                gauge_fig = create_gauge_chart(activity_index)
                st.plotly_chart(gauge_fig, width='stretch')

        st.write("")

        # Diagnostics container
        with st.container():
            st.markdown("### System Diagnostics")

            metric_col1, metric_col2, metric_col3 = st.columns(3)

            with metric_col1:
                st.metric(
                    label="Predicted Index",
                    value=f"{activity_index:.1f}"
                )

            with metric_col2:
                st.metric(
                    label="Activity Level",
                    value=risk_level
                )

            with metric_col3:
                peak_intensity = np.max(np.abs(image_array))
                st.metric(
                    label="Peak Intensity",
                    value=f"{peak_intensity:.3f}"
                )

            st.write("")

            # Activity-band summary
            st.markdown(f"""
            <div style='
                background: linear-gradient(90deg, {risk_color}40 0%, {risk_color}20 100%);
                border-left: 6px solid {risk_color};
                border-radius: 8px;
                padding: 1.2rem 1.5rem;
                margin: 1rem 0;
            '>
                <div style='display: flex; align-items: center; gap: 1rem;'>
                    <div>
                        <h4 style='margin: 0; color: {risk_color}; font-size: 1.3rem; font-weight: 700;'>
                            ACTIVITY LEVEL: {risk_level}
                        </h4>
                        <p style='margin: 0.3rem 0 0 0; color: #E0E0E0; font-size: 1rem;'>
                            {risk_desc}
                        </p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.write("")
            st.markdown("#### Magnetic Field Statistics")

            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

            with stat_col1:
                st.metric("Minimum Flux", f"{image_array.min():.2f}")
            with stat_col2:
                st.metric("Average Flux", f"{image_array.mean():.2f}")
            with stat_col3:
                st.metric("Maximum Flux", f"{image_array.max():.2f}")
            with stat_col4:
                st.metric("Std. Deviation", f"{image_array.std():.2f}")

        st.write("")
        st.write("")

        # Business context container
        with st.container():
            st.markdown("### Critical Infrastructure Protection")
            st.write("")

            context_col1, context_col2, context_col3 = st.columns(3, gap="medium")

            with context_col1:
                st.markdown("""
                <div class='info-card'>
                    <h4 style='color: #1E88E5;'>Satellite Systems</h4>
                    <p style='color: #C0C0C0; font-size: 0.9rem; line-height: 1.6;'>
                        Solar storms can damage satellite electronics. Activity estimates help
                        analysts review risk indicators alongside other space-weather data.
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with context_col2:
                st.markdown("""
                <div class='info-card'>
                    <h4 style='color: #F39C12;'>Power Grid Stability</h4>
                    <p style='color: #C0C0C0; font-size: 0.9rem; line-height: 1.6;'>
                        Geomagnetically induced currents from solar storms can cause blackouts.
                        Model output can support retrospective analysis of high-activity events.
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with context_col3:
                st.markdown("""
                <div class='info-card'>
                    <h4 style='color: #2ECC71;'>Service Continuity</h4>
                    <p style='color: #C0C0C0; font-size: 0.9rem; line-height: 1.6;'>
                        GPS, telecommunications, and air navigation systems may be affected.
                        Auralis is a local research tool for inspecting activity indicators.
                    </p>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.info("Select a data source from the sidebar to begin analysis")

        st.write("")
        st.write("")

        with st.container():
            st.markdown("### System Overview")

            st.markdown("""
            **AURALIS** is a solar activity analysis system using deep learning
            to analyze magnetograms from the HMI (Helioseismic and Magnetic Imager) instrument
            aboard NASA's SDO (Solar Dynamics Observatory) mission.

            **Technical Specifications**:
            - Architecture: Coronium V3 PRO (V3ResidualBlock + ECA attention)
            - Performance: 0.07% MAE on validation set
            - Training: 2000+ solar magnetograms
            - Inference: Local current-index estimation
            - Application: Critical infrastructure protection
            """)


if __name__ == "__main__":
    main()

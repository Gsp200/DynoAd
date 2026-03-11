from __future__ import annotations

import io
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import streamlit as st
from PIL import Image


# -------------------------------------------------
# flexible imports: renderer
# -------------------------------------------------
_RENDER_IMPORT_ERROR = None

try:
    from render.video_renderer import render_fast_ad, RenderSpec, ALL_STYLES
except Exception as e1:
    try:
        from video_renderer import render_fast_ad, RenderSpec, ALL_STYLES
    except Exception as e2:
        try:
            from src.render.video_renderer import render_fast_ad, RenderSpec, ALL_STYLES
        except Exception as e3:
            render_fast_ad = None
            RenderSpec = None
            ALL_STYLES = []
            _RENDER_IMPORT_ERROR = f"""
Renderer import failed.

Tried:
1. from render.video_renderer import ...
2. from video_renderer import ...
3. from src.render.video_renderer import ...

Errors:
- {e1}
- {e2}
- {e3}
"""


# -------------------------------------------------
# flexible imports: voice generation
# -------------------------------------------------
_VOICE_IMPORT_ERROR = None

try:
    from voice_generation import (
        generate_script_with_gemini_from_images,
        generate_elevenlabs_audio,
    )
except Exception as e1:
    try:
        from modules.voice_generation import (
            generate_script_with_gemini_from_images,
            generate_elevenlabs_audio,
        )
    except Exception as e2:
        try:
            from dynoad.voice_generation import (
                generate_script_with_gemini_from_images,
                generate_elevenlabs_audio,
            )
        except Exception as e3:
            generate_script_with_gemini_from_images = None
            generate_elevenlabs_audio = None
            _VOICE_IMPORT_ERROR = f"""
Voice generation import failed.

Tried:
1. from voice_generation import ...
2. from modules.voice_generation import ...
3. from dynoad.voice_generation import ...

Errors:
- {e1}
- {e2}
- {e3}
"""


# -------------------------------------------------
# page config
# -------------------------------------------------
st.set_page_config(
    page_title="DynoAd Ultra",
    layout="wide",
    initial_sidebar_state="collapsed",
)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AVATAR_DIR = Path("assets/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------
# custom CSS
# -------------------------------------------------
def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background: #07070c;
            color: white;
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            background:
                radial-gradient(circle at 20% 20%, rgba(109, 40, 217, 0.30), transparent 30%),
                radial-gradient(circle at 80% 80%, rgba(37, 99, 235, 0.25), transparent 30%);
            z-index: -2;
            animation: dynoadMove 14s infinite alternate ease-in-out;
            pointer-events: none;
        }

        @keyframes dynoadMove {
            0% { transform: translateY(0px); }
            100% { transform: translateY(-80px); }
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        section[data-testid="stSidebar"] {
            display: none;
        }

        .dyno-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 18px 28px;
            border: 1px solid rgba(255,255,255,.06);
            border-radius: 18px;
            background: rgba(17,17,24,.55);
            backdrop-filter: blur(12px);
            margin-bottom: 28px;
        }

        .dyno-logo {
            color: #c4b5fd;
            font-weight: 700;
            font-size: 1.25rem;
            letter-spacing: 0.2px;
        }

        .dyno-nav-links {
            display: flex;
            gap: 28px;
            color: rgba(255,255,255,.78);
            font-size: 0.95rem;
        }

        .dyno-avatar {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            background: linear-gradient(135deg, #9333ea, #3b82f6);
            box-shadow: 0 0 16px rgba(147, 51, 234, .45);
        }

        .dyno-hero {
            text-align: center;
            padding: 45px 12px 40px;
            margin-bottom: 12px;
        }

        .dyno-tag {
            display: inline-block;
            padding: 10px 16px;
            border-radius: 999px;
            background: #141420;
            border: 1px solid rgba(255,255,255,.06);
            color: #c4b5fd;
            font-size: 0.92rem;
            margin-bottom: 18px;
        }

        .dyno-hero h1 {
            font-size: clamp(2.4rem, 5vw, 4.5rem);
            line-height: 1.06;
            margin: 0;
            background: linear-gradient(90deg, #ffffff, #c4b5fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .dyno-hero p {
            max-width: 760px;
            margin: 18px auto 0;
            color: rgba(255,255,255,.72);
            font-size: 1.05rem;
            line-height: 1.7;
        }

        .dyno-card {
            background: rgba(17,17,24,.82);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,.06);
            border-radius: 20px;
            padding: 22px;
            box-shadow: 0 20px 40px rgba(0,0,0,.28);
            margin-bottom: 22px;
        }

        .dyno-card h3 {
            margin-top: 0;
            margin-bottom: 8px;
            font-size: 1.15rem;
        }

        .dyno-muted {
            color: rgba(255,255,255,.68);
            font-size: 0.95rem;
        }

        .dyno-section-title {
            font-size: 1.22rem;
            font-weight: 700;
            margin-bottom: 14px;
        }

        .dyno-script-box {
            background: #14141d;
            border: 1px solid rgba(255,255,255,.06);
            border-radius: 14px;
            padding: 16px;
            white-space: pre-wrap;
            line-height: 1.65;
            color: rgba(255,255,255,.88);
            min-height: 220px;
        }

        .dyno-preview-box {
            height: 280px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            border-radius: 16px;
            background: linear-gradient(135deg,#1c1c2b,#141422);
            border: 1px solid rgba(255,255,255,.05);
            color: rgba(255,255,255,.70);
        }

        .dyno-play {
            font-size: 2.2rem;
            margin-bottom: 10px;
        }

        .dyno-timeline-item {
            margin-bottom: 18px;
        }

        .dyno-timeline-label {
            font-size: 0.95rem;
            margin-bottom: 6px;
        }

        .dyno-bar {
            height: 8px;
            border-radius: 999px;
        }

        .purple { background:#9333ea; width:80%; }
        .blue { background:#3b82f6; width:70%; }
        .green { background:#10b981; width:60%; }
        .orange { background:#f59e0b; width:50%; }

        .dyno-tip {
            margin-top: 12px;
            color: #c4b5fd;
            font-size: 0.9rem;
        }

        .dyno-export-row {
            display: flex;
            gap: 14px;
            flex-wrap: wrap;
        }

        div[data-testid="stFileUploader"] {
            background: rgba(20,20,32,.65);
            border: 1px dashed rgba(255,255,255,.16);
            border-radius: 16px;
            padding: 6px;
        }

        div[data-testid="stFileUploader"]:hover {
            border-color: #9333ea;
        }

        .stButton > button,
        .stDownloadButton > button {
            width: 100%;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.9rem 1rem !important;
            font-weight: 600 !important;
            background: linear-gradient(90deg, #9333ea, #3b82f6) !important;
            color: white !important;
            transition: 0.25s ease !important;
            box-shadow: 0 8px 24px rgba(80, 70, 200, 0.25);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-1px) scale(1.01);
            box-shadow: 0 14px 30px rgba(80, 70, 200, 0.34);
        }

        .stSelectbox label,
        .stTextInput label,
        .stSlider label,
        .stRadio label,
        .stFileUploader label {
            color: rgba(255,255,255,.92) !important;
            font-weight: 600 !important;
        }

        .stTextInput input,
        .stSelectbox div[data-baseweb="select"] > div,
        .stTextArea textarea {
            background: #14141d !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,.08) !important;
            border-radius: 12px !important;
        }

        div[data-baseweb="tag"] {
            background: rgba(147, 51, 234, 0.2) !important;
        }

        .stSlider [data-baseweb="slider"] {
            padding-top: 10px;
        }

        .stAlert {
            border-radius: 14px;
        }

        .preview-img-wrap img {
            border-radius: 16px !important;
            border: 1px solid rgba(255,255,255,.08);
        }

        .dyno-subtle-sep {
            height: 1px;
            background: rgba(255,255,255,.05);
            margin: 12px 0 20px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------
# helpers
# -------------------------------------------------
def _read_uploaded_image(uploaded_file) -> Optional[Image.Image]:
    try:
        data = uploaded_file.getvalue()
        if not data:
            return None
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:
        return None


def _save_uploaded_audio(uploaded_audio) -> Optional[str]:
    if uploaded_audio is None:
        return None
    try:
        audio_dir = Path("temp_audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        out_path = audio_dir / uploaded_audio.name
        out_path.write_bytes(uploaded_audio.getvalue())
        return str(out_path)
    except Exception:
        return None


def _save_uploaded_video(uploaded_video) -> Optional[str]:
    if uploaded_video is None:
        return None
    try:
        video_dir = Path("temp_video")
        video_dir.mkdir(parents=True, exist_ok=True)
        out_path = video_dir / uploaded_video.name
        out_path.write_bytes(uploaded_video.getvalue())
        return str(out_path)
    except Exception:
        return None


def _load_images(uploaded_files) -> List[Image.Image]:
    images: List[Image.Image] = []
    for f in uploaded_files or []:
        img = _read_uploaded_image(f)
        if img is not None:
            images.append(img)
    return images


def _find_ffmpeg() -> Optional[str]:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_path and os.path.exists(ffmpeg_path):
            return ffmpeg_path
    except Exception:
        pass
    return None


def _resolve_default_avatar_clip(presenter_type: str) -> Optional[str]:
    avatar_map = {
        "Realistic Male": AVATAR_DIR / "real_male.mp4",
        "Realistic Female": AVATAR_DIR / "real_female.mp4",
        "Cartoon Presenter": AVATAR_DIR / "cartoon.mp4",
    }
    path = avatar_map.get(presenter_type)
    if path and path.exists():
        return str(path)
    return None


def _overlay_avatar_ffmpeg(
    base_video_path: str,
    avatar_video_path: str,
    output_path: str,
    position: str = "bottom-right",
    scale_ratio: float = 0.28,
) -> str:
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        return base_video_path

    pos_map = {
        "bottom-right": "W-w-24:H-h-24",
        "bottom-left": "24:H-h-24",
        "top-right": "W-w-24:24",
        "top-left": "24:24",
    }
    overlay_pos = pos_map.get(position, "W-w-24:H-h-24")

    filter_complex = (
        f"[1:v]scale=iw*{scale_ratio}:-1[avatar];"
        f"[0:v][avatar]overlay={overlay_pos}:shortest=1[v]"
    )

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        base_video_path,
        "-stream_loop",
        "-1",
        "-i",
        avatar_video_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-shortest",
        output_path,
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path
    except Exception:
        return base_video_path


def hero():
    st.markdown(
        """
        <div class="dyno-nav">
            <div class="dyno-logo">✨ DynoAd Ultra</div>
            <div class="dyno-nav-links">
                <div>Dashboard</div>
                <div>Templates</div>
                <div>History</div>
                <div>Settings</div>
            </div>
            <div class="dyno-avatar"></div>
        </div>

        <section class="dyno-hero">
            <div class="dyno-tag">AI Powered Advertisement Generation</div>
            <h1>Generate AI Advertisements<br>in Seconds</h1>
            <p>
                Upload product images and let AI automatically generate
                professional marketing videos with dynamic visuals, script,
                voice, music, and presenter overlays.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def open_card(title: str, subtitle: str | None = None):
    st.markdown('<div class="dyno-card">', unsafe_allow_html=True)
    st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="dyno-muted">{subtitle}</div>', unsafe_allow_html=True)


def close_card():
    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------------------------------
# checks
# -------------------------------------------------
if render_fast_ad is None or RenderSpec is None:
    st.error("Video renderer could not be imported.")
    st.code(_RENDER_IMPORT_ERROR or "Unknown renderer import error")
    st.stop()


# -------------------------------------------------
# UI start
# -------------------------------------------------
inject_custom_css()
hero()

# session defaults
if "generated_script" not in st.session_state:
    st.session_state.generated_script = ""
if "final_video_path" not in st.session_state:
    st.session_state.final_video_path = None


# -------------------------------------------------
# Main layout
# -------------------------------------------------
left_main, right_main = st.columns([1.25, 1])

with left_main:
    open_card("Upload Product Images", "Drop images here or click to upload.")
    uploaded_images = st.file_uploader(
        "Upload product images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="images_upload",
        label_visibility="collapsed",
    )
    st.markdown('<div class="dyno-tip">Pro Tip: Use clean background product images.</div>', unsafe_allow_html=True)
    close_card()

with right_main:
    open_card("Generated Advertisement", "Video preview will appear here once rendering completes.")
    if st.session_state.final_video_path and Path(st.session_state.final_video_path).exists():
        st.video(st.session_state.final_video_path)
    else:
        st.markdown(
            """
            <div class="dyno-preview-box">
                <div class="dyno-play">▶</div>
                <div>Video preview will appear here</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    close_card()

images = _load_images(uploaded_images)

if images:
    open_card("Preview Gallery", "Uploaded product images")
    preview_cols = st.columns(min(4, len(images)))
    for i, img in enumerate(images[:8]):
        with preview_cols[i % len(preview_cols)]:
            st.markdown('<div class="preview-img-wrap">', unsafe_allow_html=True)
            st.image(img, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    close_card()

settings_col, script_col, timeline_col = st.columns([1.1, 1, 1])

with settings_col:
    open_card("Customization")

    brand = st.text_input("Brand", "Dyno")
    headline = st.text_input("Headline", "NEW ARRIVAL")
    tagline = st.text_input("Tagline", "Premium design. Smart styling.")
    cta = st.text_input("CTA", "SHOP NOW")

    format_choice = st.selectbox(
        "Video Format",
        ["Vertical (720×1280)", "Square (1080×1080)", "Landscape (1280×720)"],
        index=0,
    )

    fps = st.slider("FPS", min_value=8, max_value=30, value=12, step=1)
    total_duration = st.slider("Total Duration (seconds)", min_value=6, max_value=24, value=12, step=1)

    style = st.selectbox(
        "Ad Style",
        ALL_STYLES if ALL_STYLES else ["Cinematic Hero Reveal"],
        index=0,
    )

    uploaded_logo = st.file_uploader(
        "Upload logo (optional)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=False,
        key="logo_upload",
    )

    st.markdown('<div class="dyno-subtle-sep"></div>', unsafe_allow_html=True)

    audio_mode = st.radio(
        "Audio Source",
        [
            "No Audio",
            "Upload Background Music",
            "AI Voiceover (Gemini + ElevenLabs)",
        ],
        index=0,
    )

    uploaded_music = None
    voice_tone = "Luxury & Premium"

    if audio_mode == "Upload Background Music":
        uploaded_music = st.file_uploader(
            "Upload music",
            type=["mp3", "wav", "m4a", "aac", "ogg"],
            accept_multiple_files=False,
            key="music_uploader",
        )

    elif audio_mode == "AI Voiceover (Gemini + ElevenLabs)":
        voice_tone = st.selectbox(
            "Voiceover Tone",
            [
                "Luxury & Premium",
                "Energetic & Bold",
                "Minimal & Clean",
                "Tech & Futuristic",
                "Warm & Friendly",
            ],
            index=0,
        )

        if generate_script_with_gemini_from_images is None or generate_elevenlabs_audio is None:
            st.warning("Voice generation module could not be imported.")
            if _VOICE_IMPORT_ERROR:
                st.caption("Check your voice_generation.py import path.")

    music_volume = st.slider("Audio Volume", min_value=0.0, max_value=1.0, value=0.20, step=0.01)
    music_fade_in = st.slider("Fade In (sec)", min_value=0.0, max_value=3.0, value=0.5, step=0.1)
    music_fade_out = st.slider("Fade Out (sec)", min_value=0.0, max_value=3.0, value=0.8, step=0.1)

    st.markdown('<div class="dyno-subtle-sep"></div>', unsafe_allow_html=True)

    avatar_mode = st.selectbox(
        "Avatar Mode",
        ["No Avatar", "Side Presenter Overlay"],
        index=0,
    )

    presenter_type = "Realistic Male"
    avatar_source = "Use built-in avatar"
    uploaded_avatar_video = None
    avatar_position = "bottom-right"
    avatar_scale = 0.28

    if avatar_mode == "Side Presenter Overlay":
        presenter_type = st.selectbox(
            "Presenter Type",
            ["Realistic Male", "Realistic Female", "Cartoon Presenter"],
            index=0,
        )

        avatar_source = st.radio(
            "Avatar Source",
            ["Use built-in avatar", "Upload my own avatar clip"],
            index=0,
        )

        if avatar_source == "Upload my own avatar clip":
            uploaded_avatar_video = st.file_uploader(
                "Upload avatar video",
                type=["mp4", "mov", "m4v"],
                accept_multiple_files=False,
                key="avatar_video_upload",
            )

        avatar_position = st.selectbox(
            "Avatar Position",
            ["bottom-right", "bottom-left", "top-right", "top-left"],
            index=0,
        )

        avatar_scale = st.slider(
            "Avatar Size",
            min_value=0.18,
            max_value=0.40,
            value=0.28,
            step=0.01,
        )

    close_card()

with script_col:
    open_card("AI Generated Script")
    script_text = st.session_state.generated_script.strip() or (
        "Scene 1 (0-5s)\nIntroducing the future of innovation\n\n"
        "Scene 2 (5-10s)\nCrafted with precision and excellence\n\n"
        "Scene 3 (10-15s)\nExperience the difference today"
    )
    st.markdown(f'<div class="dyno-script-box">{script_text}</div>', unsafe_allow_html=True)
    close_card()

with timeline_col:
    open_card("Advertisement Timeline")
    st.markdown(
        """
        <div class="dyno-timeline-item">
            <div class="dyno-timeline-label">Opening Scene</div>
            <div class="dyno-bar purple"></div>
        </div>
        <div class="dyno-timeline-item">
            <div class="dyno-timeline-label">Product Showcase</div>
            <div class="dyno-bar blue"></div>
        </div>
        <div class="dyno-timeline-item">
            <div class="dyno-timeline-label">Call to Action</div>
            <div class="dyno-bar green"></div>
        </div>
        <div class="dyno-timeline-item">
            <div class="dyno-timeline-label">Brand Outro</div>
            <div class="dyno-bar orange"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    close_card()


# -------------------------------------------------
# Generate button
# -------------------------------------------------
generate_now = st.button("✨ Generate Advertisement", use_container_width=True)

logo = _read_uploaded_image(uploaded_logo) if uploaded_logo is not None else None

if generate_now:
    if not images:
        st.error("Please upload at least one valid product image.")
        st.stop()

    if format_choice == "Vertical (720×1280)":
        size = (720, 1280)
    elif format_choice == "Square (1080×1080)":
        size = (1080, 1080)
    else:
        size = (1280, 720)

    out_path = OUTPUT_DIR / "dynoad_output.mp4"

    final_audio_path = None
    generated_script = ""

    if audio_mode == "Upload Background Music":
        final_audio_path = _save_uploaded_audio(uploaded_music)
        if uploaded_music is not None and not final_audio_path:
            st.warning("Music file could not be saved. Video will be generated without audio.")

    elif audio_mode == "AI Voiceover (Gemini + ElevenLabs)":
        if generate_script_with_gemini_from_images is None or generate_elevenlabs_audio is None:
            st.warning("Voice generation module is not available. Video will be generated without audio.")
        else:
            with st.spinner("Generating AI voiceover..."):
                script_result = generate_script_with_gemini_from_images(
                    images=images,
                    tone=voice_tone,
                    brand=brand,
                    cta=cta,
                )

                generated_script = script_result.get("script", "").strip()

                if generated_script:
                    voice_result = generate_elevenlabs_audio(
                        script=generated_script,
                        output_path=str(OUTPUT_DIR / "voiceover.mp3"),
                    )
                    final_audio_path = voice_result.get("audio_path")
                else:
                    st.warning(
                        "Script generation failed. Video will be created without voiceover.\n\n"
                        f"Details: {script_result.get('error', 'Unknown error')}"
                    )

    spec = RenderSpec(
        size=size,
        fps=fps,
        total_duration=total_duration,
        brand=brand,
        headline=headline,
        tagline=tagline,
        cta=cta,
        style=style,
        music_path=final_audio_path,
        music_volume=1.0 if audio_mode == "AI Voiceover (Gemini + ElevenLabs)" and final_audio_path else music_volume,
        music_fade_in=0.0 if audio_mode == "AI Voiceover (Gemini + ElevenLabs)" and final_audio_path else music_fade_in,
        music_fade_out=0.0 if audio_mode == "AI Voiceover (Gemini + ElevenLabs)" and final_audio_path else music_fade_out,
    )

    try:
        with st.spinner("Rendering ad video..."):
            result_path = render_fast_ad(
                images=images,
                logo=logo,
                spec=spec,
                out_path=str(out_path),
            )

        final_video_path = str(result_path)

        if avatar_mode == "Side Presenter Overlay":
            avatar_clip_path = None

            if avatar_source == "Use built-in avatar":
                avatar_clip_path = _resolve_default_avatar_clip(presenter_type)
                if not avatar_clip_path:
                    st.warning(
                        f"No built-in avatar found for '{presenter_type}'. "
                        f"Put files in assets/avatars/: real_male.mp4, real_female.mp4, cartoon.mp4."
                    )
            else:
                avatar_clip_path = _save_uploaded_video(uploaded_avatar_video)
                if uploaded_avatar_video is not None and not avatar_clip_path:
                    st.warning("Avatar video could not be saved.")

            if avatar_clip_path and Path(avatar_clip_path).exists():
                with st.spinner("Adding avatar presenter..."):
                    avatar_output = str(OUTPUT_DIR / "dynoad_with_avatar.mp4")
                    final_video_path = _overlay_avatar_ffmpeg(
                        base_video_path=final_video_path,
                        avatar_video_path=avatar_clip_path,
                        output_path=avatar_output,
                        position=avatar_position,
                        scale_ratio=avatar_scale,
                    )

        st.session_state.generated_script = generated_script
        st.session_state.final_video_path = final_video_path

        st.success("Ad generated successfully!")
        st.rerun()

    except Exception as e:
        st.exception(e)


# -------------------------------------------------
# Export & Share
# -------------------------------------------------
open_card("Export & Share")

if st.session_state.final_video_path and Path(st.session_state.final_video_path).exists():
    export_col1, export_col2, export_col3 = st.columns(3)

    with export_col1:
        with open(st.session_state.final_video_path, "rb") as f:
            st.download_button(
                "⬇ Download Video",
                data=f,
                file_name=Path(st.session_state.final_video_path).name,
                mime="video/mp4",
                use_container_width=True,
            )

    with export_col2:
        st.button("🔗 Share", use_container_width=True)

    with export_col3:
        st.button("✏️ Edit Video", use_container_width=True)
else:
    st.info("Generate an advertisement first to enable export options.")

close_card()
import streamlit as st
import os
import time
from dotenv import load_dotenv
from utils.downloader import download_audio_from_youtube
from utils.transcriber import transcribe_audio
from utils.summarizer import generate_blog
import static_ffmpeg  # Import static_ffmpeg to ensure it's initialized

# Load environment variables
load_dotenv(override=True)

# Debug: Print environment variables (remove in production)
print("Environment variables loaded:")
print(f"OPENAI_API_KEY present: {'OPENAI_API_KEY' in os.environ}")
print(f"OPENAI_API_KEY starts with: {os.environ.get('OPENAI_API_KEY', '')[:5]}..." if 'OPENAI_API_KEY' in os.environ else "No OPENAI_API_KEY found")

# Initialize static_ffmpeg
static_ffmpeg.add_paths()

# Set page config
st.set_page_config(
    page_title="Card Making Ideas & YouTube to Blog",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        max-width: 900px;
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stTextArea>div>div>textarea {
        min-height: 150px;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    </style>
""", unsafe_allow_html=True)

# Card Making Ideas & YouTube to Blog

# Section 1: Card Making Ideas: Planning Agent
st.header("🎨 Card Making Ideas: Planning Agent")

# Initialize session state for card ideas
if 'card_ideas' not in st.session_state:
    st.session_state.card_ideas = []
    
# Generate card ideas
def generate_card_ideas():
    # List of card making ideas
    themes = ["Birthday", "Thank You", "Wedding", "Anniversary", "Sympathy", "Graduation", "New Baby", "Holiday"]
    techniques = ["Watercolor", "Embossing", "Die-cutting", "Stamping", "Quilling", "Pop-up", "Interactive"]
    styles = ["Vintage", "Modern", "Minimalist", "Whimsical", "Elegant", "Rustic", "Shabby Chic"]
    
    import random
    ideas = []
    for _ in range(5):  # Generate 5 ideas
        theme = random.choice(themes)
        technique = random.choice(techniques)
        style = random.choice(styles)
        idea = f"**{theme} Card**: Create a {style.lower()} card using {technique.lower()} technique. "
        idea += f"Focus on {random.choice(['warm', 'cool', 'pastel', 'bold', 'monochromatic'])} colors. "
        idea += random.choice([
            "Add some hand-lettered sentiments for a personal touch.",
            "Incorporate some die-cut elements for dimension.",
            "Use patterned paper to create interesting layers.",
            "Add some bling with rhinestones or sequins.",
            "Try a unique fold for added interest."
        ])
        ideas.append(idea)
    return ideas

# Generate ideas button
if st.button("🎲 Generate Card Making Ideas"):
    st.session_state.card_ideas = generate_card_ideas()
    st.session_state.show_next_steps = True

# Display card ideas
if st.session_state.card_ideas:
    st.markdown("### This Week's Card Making Ideas")
    for i, idea in enumerate(st.session_state.card_ideas, 1):
        st.markdown(f"{i}. {idea}")
    
    # Show next steps
    if st.session_state.get('show_next_steps', False):
        st.markdown("---")
        st.markdown("### Next Steps")
        st.markdown("""
        Thank you for generating your card making ideas! Here's what to do next:
        
        1. Select an idea that inspires you the most
        2. Create a video tutorial showcasing your card making process
        3. Upload your video to YouTube
        4. Copy the video URL and paste it in the section below to transform it into a blog post
        
        We can't wait to see your creative process in action!
        """)

# Divider between sections
st.markdown("---")

# Section 2: YouTube to Blog: Content Agent
st.header("🎥 YouTube to Blog: Content Agent")
st.markdown("""
    Transform YouTube videos into engaging blog posts with AI. 
    Simply paste a YouTube URL, and let the magic happen!
""")

# Sidebar for additional options
with st.sidebar:
    st.header("Settings")
    
    # Tone selection
    tone = st.selectbox(
        "Select Blog Tone",
        ["Professional", "Casual", "Educational", "Persuasive"],
        index=0,
        help="Select the tone for your blog post"
    )
    
    # Model selection
    model_size = st.selectbox(
        "Whisper Model Size",
        ["tiny", "base", "small", "medium", "large"],
        index=1,
        help="Larger models are more accurate but slower"
    )
    
    # Additional options
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This app uses:
    - [OpenAI Whisper](https://openai.com/research/whisper) for audio transcription
    - [OpenAI GPT](https://openai.com) for blog post generation
    - [Streamlit](https://streamlit.io) for the web interface
    - [pytube](https://pytube.io) for YouTube video downloading
    - [moviepy](https://zulko.github.io/moviepy/) for audio extraction
    """)

# Main content area
col1, col2 = st.columns([3, 1])

# URL input
url = st.text_input("YouTube Video URL or ID", "", placeholder="https://www.youtube.com/watch?v=...")
    
# Process button
process_clicked = st.button("Generate Blog Post")

# Initialize session state
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'blog_post' not in st.session_state:
    st.session_state.blog_post = ""

# Main processing logic
if process_clicked and url:
    with st.spinner("Processing your request..."):
        try:
            # Step 1: Download audio
            with st.status("Downloading audio...", expanded=True) as status:
                try:
                    audio_path = download_audio_from_youtube(url)
                    if not audio_path or not os.path.exists(audio_path):
                        raise Exception("Failed to download audio file")
                    status.update(label="✅ Audio downloaded", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="❌ Error downloading audio", state="error")
                    st.error(f"Error downloading audio: {str(e)}")
                    st.stop()
            
            # Step 2: Transcribe audio
            with st.status("Transcribing audio...", expanded=True) as status:
                try:
                    st.session_state.transcript = transcribe_audio(audio_path, model_size)
                    if not st.session_state.transcript:
                        raise Exception("Transcription returned empty result")
                    status.update(label="✅ Transcription complete", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="❌ Error transcribing audio", state="error")
                    st.error(f"Error transcribing audio: {str(e)}")
                    st.stop()
            
            # Step 3: Generate blog post
            with st.status("Generating blog post...", expanded=True) as status:
                try:
                    result = generate_blog(st.session_state.transcript, tone=tone)
                    if result.get('status') == 'error':
                        raise Exception(result.get('message', 'Unknown error generating blog post'))
                    
                    st.session_state.blog_post = result.get('blog_post', '')
                    if not st.session_state.blog_post:
                        raise Exception("Blog post generation returned empty result")
                        
                    status.update(label="✅ Blog post generated", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="❌ Error generating blog post", state="error")
                    st.error(f"Error generating blog post: {str(e)}")
                    st.stop()
            
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

# Display results
if st.session_state.transcript:
    st.markdown("---")
    st.markdown("## 📝 Transcript")
    st.text_area("", value=st.session_state.transcript, height=200, disabled=True)

if st.session_state.blog_post:
    # Add a divider
    st.markdown("---")
    
    # Blog post header
    st.markdown("## ✨ Generated Blog Post")
    
    # Blog post content
    st.markdown(st.session_state.blog_post)
    
    # Download button
    st.download_button(
        label="Download as Markdown",
        data=st.session_state.blog_post,
        file_name="generated_blog_post.md",
        mime="text/markdown"
    )
    
    # Copy to clipboard button
    if st.button("Copy to Clipboard"):
        st.session_state.copied = True
        st.experimental_rerun()
    
    if st.session_state.get('copied', False):
        st.success("Blog post copied to clipboard!")
        st.session_state.copied = False

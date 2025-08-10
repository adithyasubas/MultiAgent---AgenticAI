# 🎨 Card Making Ideas & YouTube to Blog

A versatile Streamlit application that combines two powerful tools:
1. **Card Making Ideas Generator** - Get creative card making ideas with themes, color schemes, and design tips
2. **YouTube to Blog Generator** - Transform any YouTube video into a well-structured blog post

## 🚀 Features

### 🎨 Card Making Ideas: Planner Agent
- Generate unique card making ideas with themes and color schemes
- Get creative design tips and techniques
- Multiple card style options (Greeting, Thank You, Birthday, etc.)
- Save and organize your favorite ideas

### 🎥 YouTube to Blog: Content Agent
- Download audio from any YouTube video
- Accurate speech-to-text transcription using Whisper
- AI-powered blog post generation using OpenAI's GPT model
- Multiple tone options (Professional, Casual, Educational, Persuasive)
- Clean, responsive UI
- Export blog as Markdown

## 🛠️ Prerequisites

- Python 3.8+
- OpenAI API key (for AI features)
- FFmpeg (for audio processing)
- Streamlit (for the web interface)

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/youtube-to-blog.git
   cd youtube-to-blog
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## 🏃‍♂️ Running the Application

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Open your browser and navigate to `http://localhost:8501`

3. Use the sidebar to navigate between:
   - 🎨 Card Making Ideas
   - 🎥 YouTube to Blog

4. For YouTube to Blog:
   - Paste a YouTube URL and click "Generate Blog"
   
5. For Card Making Ideas:
   - Click "🎲 Generate Card Making Ideas" to get creative suggestions

## 📝 Usage

### 🎥 YouTube to Blog: Content Agent
1. Navigate to the YouTube to Blog section
2. Paste a YouTube video URL in the input field
3. Select your preferred tone from the sidebar
4. Click "Generate Blog"
5. Wait for the process to complete
6. View, copy, or download the generated blog post

### 🎨 Card Making Ideas: Planner Agent
1. Navigate to the Card Making Ideas section
2. Click "🎲 Generate Card Making Ideas"
3. Browse through the generated ideas
4. Get inspiration for your next card making project

## 📂 Project Structure

```
card-blog-generator/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (create this file)
└── utils/
    ├── downloader.py     # Handles YouTube audio download
    ├── transcriber.py    # Handles speech-to-text transcription
    └── summariser.py     # Generates blog posts from transcripts
```

## ⚠️ Notes

### For YouTube to Blog:
- The first run will download the Whisper model (approximately 1-2GB)
- Processing time depends on video length and your internet connection
- For longer videos, the process might take several minutes
- Make sure you have sufficient storage space for downloaded audio files

### For Card Making Ideas:
- Internet connection is required to fetch new ideas
- Generated ideas are meant for inspiration and can be customized

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

- [OpenAI](https://openai.com/) for Whisper and GPT models
- [Streamlit](https://streamlit.io/) for the web framework
- [pytube](https://pytube.io/) for YouTube downloads
- [static-ffmpeg](https://github.com/kkroening/ffmpeg-python) for audio processing

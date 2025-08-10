import os
import re
import time
import yt_dlp
from moviepy.editor import AudioFileClip
import static_ffmpeg
from urllib.parse import urlparse, parse_qs
import random
import string

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    # Handle youtu.be URLs
    if 'youtu.be' in url:
        return url.split('/')[-1].split('?')[0]
    
    # Handle youtube.com URLs
    parsed = urlparse(url)
    if 'youtube.com' in parsed.netloc:
        if 'v=' in parsed.query:
            return parse_qs(parsed.query)['v'][0]
        elif parsed.path.startswith('/embed/'):
            return parsed.path.split('/')[2]
    
    # If no video ID found, return the input as is (might be a video ID)
    return url

def download_video(url, output_dir="downloads"):
    """
    Downloads a YouTube video and returns the file path.
    
    Args:
        url (str): YouTube video URL or video ID
        output_dir (str): Directory to save the video file
        
    Returns:
        str: Path to the downloaded video file
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Processing URL: {url}")
        
        # If it's not a full URL, assume it's a video ID
        if not url.startswith(('http://', 'https://')):
            url = f"https://www.youtube.com/watch?v={url}"
        
        # Use the retry mechanism to download the video
        video_path = download_with_retry(url, output_dir)
        
        if not os.path.exists(video_path):
            raise FileNotFoundError("Failed to download video")
            
        print(f"Download complete: {video_path}")
        return video_path
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'private' in error_msg or 'unavailable' in error_msg:
            raise Exception("The video is unavailable. It may be private, removed, or age-restricted.")
        elif 'unable to download webpage' in error_msg:
            raise Exception("Could not access YouTube. Please check your internet connection.")
        elif 'sign in to confirm your age' in error_msg:
            raise Exception("This video is age-restricted and cannot be downloaded.")
        elif 'http error 400' in error_msg:
            raise Exception("Invalid request. The video might be private or unavailable in your region.")
        elif 'http error 403' in error_msg:
            raise Exception("Access denied. YouTube might be rate-limiting your requests. Please try again later.")
        else:
            raise Exception(f"Error downloading video: {str(e)}")

def convert_to_mp3(video_path):
    """
    Converts a video file to MP3 format.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        str: Path to the converted MP3 file
    """
    try:
        # Initialize static_ffmpeg
        static_ffmpeg.add_paths()
        
        # Generate output path
        audio_path = os.path.splitext(video_path)[0] + ".mp3"
        
        # Skip if audio file already exists
        if os.path.exists(audio_path):
            print(f"Audio file already exists: {audio_path}")
            return audio_path
            
        print(f"Converting video to MP3: {video_path}")
        
        # Load the video file
        clip = VideoFileClip(video_path)
        
        # Write the audio to file
        clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
        
        # Close the clip to free resources
        clip.close()
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError("Failed to convert video to MP3")
            
        print(f"Conversion complete: {audio_path}")
        return audio_path
        
    except Exception as e:
        raise Exception(f"Error converting video to MP3: {str(e)}")

def get_youtube_object(url, attempt):
    """Helper function to create YouTube object with different configurations"""
    # Different headers for each attempt
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    # Select user agent based on attempt number
    user_agent = user_agents[attempt % len(user_agents)]
    
    # Different approaches based on attempt number
    if attempt == 0:
        # First try: Standard approach
        print("Attempting standard download...")
        return pytube.YouTube(url, use_oauth=False, allow_oauth_cache=True)
    elif attempt == 1:
        # Second try: With age gate bypass
        print("Attempting with age gate bypass...")
        yt = pytube.YouTube(url, use_oauth=False, allow_oauth_cache=True)
        yt.bypass_age_gate()
        return yt
    else:
        # Third try: With different parameters
        print("Attempting with different parameters...")
        yt = pytube.YouTube(
            url,
            use_oauth=False,
            allow_oauth_cache=True
        )
        yt.bypass_age_gate()
        yt.prefetch()
        yt.descramble()
        return yt

def download_with_retry(url, output_dir, max_retries=3):
    """
    Try different approaches to download a video with retries.
    
    Args:
        url (str): YouTube video URL
        output_dir (str): Output directory
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        str: Path to the downloaded video file
    """
    last_error = None
    video_id = extract_video_id(url)
    
    for attempt in range(max_retries):
        try:
            print(f"\n--- Attempt {attempt + 1} of {max_retries} ---")
            
            # Get YouTube object with different configurations
            yt = get_youtube_object(url, attempt)
            
            # Print video title for debugging
            print(f"Video title: {yt.title}")
            
            # Define the output filename
            output_file = f"youtube_{video_id}.mp4"
            output_path = os.path.join(output_dir, output_file)
            
            # List of stream filters to try in order
            stream_filters = [
                {'progressive': True, 'file_extension': 'mp4'},  # Try progressive first
                {'adaptive': True, 'file_extension': 'mp4'},     # Then adaptive
                {}  # Finally, try any stream
            ]
            
            for stream_filter in stream_filters:
                try:
                    # Get the best available stream for the current filter
                    if stream_filter:
                        print(f"Trying stream with filter: {stream_filter}")
                        stream = (
                            yt.streams.filter(**stream_filter)
                            .order_by('resolution')
                            .desc()
                            .first()
                        )
                    else:
                        print("Trying any available stream...")
                        stream = yt.streams.first()
                    
                    if not stream:
                        print("No stream found with current filter")
                        continue
                        
                    print(f"Found stream: {stream}")
                    
                    # Add a small delay before downloading
                    time.sleep(1)
                    
                    # Download the stream
                    print(f"Downloading...")
                    stream.download(output_path=output_dir, filename=output_file)
                    
                    # Verify the file was downloaded
                    if os.path.exists(output_path):
                        file_size = os.path.getsize(output_path) / (1024 * 1024)  # Size in MB
                        print(f"Successfully downloaded to: {output_path} ({file_size:.2f} MB)")
                        
                        # Verify the file is not empty or corrupted
                        if file_size > 0.1:  # At least 100KB
                            return output_path
                        else:
                            print("File is too small, may be corrupted. Retrying...")
                            os.remove(output_path)
                            continue
                            
                except Exception as e:
                    print(f"Error downloading stream: {str(e)}")
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    continue
            
            raise Exception("No suitable streams found for this video after all attempts")
                    
        except Exception as e:
            last_error = e
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            time.sleep(2)  # Wait before retrying
    
    # If we get here, all attempts failed
    if last_error:
        raise Exception(f"All download attempts failed. Last error: {str(last_error)}")
    raise Exception("All download attempts failed")

def get_random_string(length=8):
    """Generate a random string of fixed length"""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def download_audio_from_youtube(url, output_dir="downloads"):
    """
    Downloads audio from a YouTube video using yt-dlp.
    
    Args:
        url (str): YouTube video URL or video ID
        output_dir (str): Directory to save the audio file
        
    Returns:
        str: Path to the downloaded audio file
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Clean and validate the URL
        if not url:
            raise ValueError("No URL provided")
            
        # If it's not a full URL, assume it's a video ID
        if not url.startswith(('http://', 'https://')):
            url = f"https://www.youtube.com/watch?v={url}"
        
        print(f"Starting download for URL: {url}")
        
        # Generate a unique output filename
        random_str = get_random_string()
        output_template = os.path.join(output_dir, f'%(title)s_{random_str}.%(ext)s')
        
        # yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',  # Choose the best audio quality
            'outtmpl': output_template,  # Output template
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,  # Show progress
            'no_warnings': False,  # Show warnings
            'ignoreerrors': False,  # Don't ignore errors
            'extract_flat': False,  # Don't extract flat
            'force_generic_extractor': False,  # Don't force generic extractor
            'nocheckcertificate': True,  # Don't check SSL certificate
            'source_address': '0.0.0.0',  # Bind to all interfaces
            'extract_retries': 3,  # Retry on extraction errors
            'retries': 10,  # Number of retries for HTTP requests
            'fragment_retries': 10,  # Number of retries for fragments
            'skip_unavailable_fragments': True,  # Skip unavailable fragments
            'keep_fragments': False,  # Don't keep fragments after download
            'no_color': False,  # Keep colors in output
            'cachedir': False,  # Disable caching
            'no_cache_dir': True,  # Don't use cache directory
            'noplaylist': True,  # Download only the video, not the playlist
            'geo_bypass': True,  # Bypass geographic restrictions
            'geo_bypass_country': 'US',  # Bypass to US
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'DNT': '1',
            },
        }
        
        # Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise Exception("Failed to extract video info")
                
                # Find the downloaded file
                downloaded_files = [f for f in os.listdir(output_dir) if f.endswith('.mp3') and f.startswith(info['title'])]
                if not downloaded_files:
                    raise FileNotFoundError("Downloaded MP3 file not found")
                
                audio_path = os.path.join(output_dir, downloaded_files[0])
                print(f"Successfully downloaded audio to: {audio_path}")
                return audio_path
                
            except Exception as e:
                error_msg = str(e).lower()
                print(f"Error in yt-dlp download: {error_msg}")
                
                # Provide more user-friendly error messages
                if 'private' in error_msg or 'unavailable' in error_msg:
                    raise Exception("The video is unavailable. It may be private, removed, or age-restricted.")
                elif 'unable to download webpage' in error_msg or 'unable to download' in error_msg:
                    raise Exception("Could not access YouTube. Please check your internet connection.")
                elif 'sign in to confirm your age' in error_msg or 'age restricted' in error_msg:
                    raise Exception("This video is age-restricted and cannot be downloaded.")
                elif 'http error 400' in error_msg or '400' in error_msg:
                    raise Exception("Invalid request. The video might be private or unavailable in your region.")
                elif 'http error 403' in error_msg or '403' in error_msg or 'rate limit' in error_msg:
                    raise Exception("Access denied. YouTube might be rate-limiting your requests. Please try again later.")
                else:
                    raise Exception(f"Error downloading audio: {str(e)}")
    
    except Exception as e:
        # Clean up any partial downloads
        if 'downloaded_files' in locals():
            for f in downloaded_files:
                try:
                    os.remove(os.path.join(output_dir, f))
                except:
                    pass
        raise  # Re-raise the exception

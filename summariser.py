import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_blog(transcript, tone="professional"):
    """
    Generate a blog post from a transcript using OpenAI's GPT model.
    
    Args:
        transcript (str): The transcript text
        tone (str): Tone of the blog post (e.g., professional, casual, educational)
        
    Returns:
        str: Generated blog post
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    try:
        prompt = f"""
        Convert the following transcript into a well-structured, {tone}-toned blog post.
        The blog should be engaging, well-organised with clear sections and subheadings.
        Remove filler words and make it easy to read.
        
        Transcript:
        {transcript}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional content writer who creates engaging blog posts from video transcripts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error generating blog: {str(e)}")

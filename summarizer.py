import os
from openai import OpenAI
from typing import Dict, Optional
import tiktoken
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text string.
    
    Args:
        text (str): The text to count tokens for
        
    Returns:
        int: Number of tokens
    """
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    return len(encoding.encode(text))

def generate_blog(transcript: str, tone: str = "professional") -> Dict[str, str]:
    """
    Generate a blog post from a transcript using OpenAI's API.
    
    Args:
        transcript (str): The transcript text to summarize
        tone (str): The tone of the blog post (professional, casual, educational, persuasive)
        
    Returns:
        Dict[str, str]: Dictionary containing the generated blog post and metadata
    """
    # Define tone instructions
    tone_instructions = {
        "professional": "Write in a professional, business-appropriate tone.",
        "casual": "Write in a casual, conversational tone.",
        "educational": "Write in an informative, educational tone suitable for teaching.",
        "persuasive": "Write in a persuasive, compelling tone that convinces the reader."
    }
    
    # Default to professional if invalid tone is provided
    if tone not in tone_instructions:
        tone = "professional"
    
    # Prepare the prompt
    prompt = f"""
    Please convert the following transcript from a YouTube video into a well-structured blog post.
    {tone_instructions[tone]}
    
    The blog post should include:
    1. An engaging introduction
    2. Clear sections with headings
    3. Key points from the transcript
    4. A conclusion that summarizes the main points
    5. A call-to-action or thought-provoking question
    
    Transcript:
    {transcript}
    """
    
    try:
        # Calculate token count and handle long transcripts
        token_count = count_tokens(prompt)
        max_tokens = 4000  # Leave room for the response
        
        if token_count > 3000:  # Approximate token limit for context
            # Truncate the transcript if it's too long
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            truncated_transcript = encoding.decode(encoding.encode(transcript)[:3000])
            prompt = prompt.replace(transcript, truncated_transcript)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional content writer who creates engaging blog posts from video transcripts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7,
        )
        
        # Extract the generated blog post
        blog_content = response.choices[0].message.content.strip()
        
        return {
            "status": "success",
            "blog_post": blog_content,
            "tokens_used": response.usage.total_tokens,
            "model": response.model,
            "tone": tone
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

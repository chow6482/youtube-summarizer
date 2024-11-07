from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from urllib.parse import urlparse, parse_qs
import config
import re

app = Flask(__name__)
client = OpenAI(api_key=config.OPENAI_API_KEY)

def extract_video_id(url):
    """Extract the video ID from various forms of YouTube URLs."""
    # Handle different YouTube URL formats
    if match := re.search(r'(?:v=|\/)([\w-]{11})', url):
        return match.group(1)
    elif match := re.search(r'(?:youtu\.be\/)([\w-]{11})', url):
        return match.group(1)
    return None

def get_transcript(video_id):
    """Get the transcript for a given video ID."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_generated_transcript(['en']).fetch()
        return " ".join(item['text'] for item in transcript)
    except Exception as e:
        raise Exception(f"Error getting transcript: {str(e)}")

def get_summary(text):
    """Get summary from OpenAI API."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialized in summarizing videos. Provide a concise but comprehensive summary."},
                {"role": "user", "content": "Summarize the following video transcript:"},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error getting summary: {str(e)}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        url = request.json.get('url', '')
        if not url:
            return jsonify({'error': 'Please provide a YouTube URL'}), 400
        
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        transcript = get_transcript(video_id)
        summary = get_summary(transcript)
        
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
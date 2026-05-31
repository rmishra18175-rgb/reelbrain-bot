from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import anthropic
import yt_dlp
import openai
import os

app = Flask(__name__)

def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '/tmp/audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return '/tmp/audio.mp3'

def transcribe_audio(file_path):
    client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    with open(file_path, 'rb') as f:
        transcript = client.audio.transcriptions.create(
            model='whisper-1', file=f
        )
    return transcript.text

def summarize_text(text):
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    message = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=100,
        messages=[{
            'role': 'user',
            'content': f'Give a single line summary in simple Hindi or English of this content: {text}'
        }]
    )
    return message.content[0].text

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming = request.form.get('Body', '').strip()
    resp = MessagingResponse()
    msg = resp.message()

    if 'youtube.com' in incoming or 'youtu.be' in incoming:
        try:
            audio_path = download_audio(incoming)
            text = transcribe_audio(audio_path)
            summary = summarize_text(text)
            msg.body(f'ReelBrain Summary: {summary}')
        except Exception as e:
            msg.body('Sorry, could not process this link. Please try again.')
    else:
        msg.body('Please send a YouTube Shorts or YouTube video link!')

    return str(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

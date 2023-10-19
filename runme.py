from pytube import YouTube
import os
import openai
import subprocess

def download_youtube_audio(url, file_path="temp_audio.wav"):
    yt = YouTube(url)
    stream = yt.streams.filter(only_audio=True).first()
    temp_file = stream.download(output_path='.', filename='temp_audio')
    
    # Convert the downloaded file to WAV format with automatic overwrite
    subprocess.run(["ffmpeg", "-y", "-i", temp_file, file_path])
    
    # Optionally, remove the original downloaded file to save space
    os.remove(temp_file)

openai.api_key = "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"

def transcribe_audio(file_path):
    print("Attempting to transcribe:", file_path)
    
    output_directory = 'split_audio'
    os.makedirs(output_directory, exist_ok=True)
    split_files_pattern = os.path.join(output_directory, "out%03d.wav")
    split_command = [
        'ffmpeg',
        '-i', file_path,
        '-f', 'segment',
        '-segment_time', '120',
        '-c', 'copy',
        split_files_pattern
    ]
    subprocess.run(split_command)
    
    transcriptions = []
    
    for segment_file in sorted(os.listdir(output_directory)):
        if segment_file.startswith("out"):
            segment_path = os.path.join(output_directory, segment_file)
            try:
                with open(segment_path, "rb") as file:
                    transcription = openai.Audio.transcribe("whisper-1", file)
                    transcriptions.append(transcription['text'])
                    print(f"Transcription for {segment_file} successful!")
            except openai.error.RateLimitError:
                print("OpenAI API rate limit reached. Please try again later or check your subscription plan.")
            except Exception as e:
                print(f"Error during transcription of {segment_file}:", str(e))
    
    full_transcription = " ".join(transcriptions)
    return full_transcription

def main():
    youtube_link = input("Please insert YouTube's URL: ")
    download_youtube_audio(youtube_link)
    transcription = transcribe_audio("temp_audio.wav")
    if not transcription:
        print("Transcription failed.")
        return

    while True:
        question = input("\nType your question here (or type 'quit' to exit): \n")
        if question.lower() == 'quit':
            print("Exiting program.")
            break

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": transcription + " " + question}
            ]
        )
        chatgpt_response = response.choices[0].message['content']
        print(f"Answer: \n {chatgpt_response}")

if __name__ == "__main__":
    main()

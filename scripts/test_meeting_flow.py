
import os
import sys
import time
from dotenv import load_dotenv

# Add project root to path
# Assuming we are running from project root or scripts folder, adjust path to src
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.transcription.groq_client import GroqTranscriber
from src.transcription.assemblyai_client import AssemblyAITranscriber
from src.transcription.report_generator import ReportGenerator
from src.transcription.openrouter_client import OpenRouterClient
from src.profiles.recording_profiles import REUNIAO_VISATION, RecordingProfile
from src.integrations.telegram_sender import TelegramSender
from src.transcription.exporters import save_meeting_report, save_rich_transcript, save_text_transcript

def main():
    print(f"Project Root: {PROJECT_ROOT}")
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

    # Configuration
    AUDIO_FILE = os.path.join(PROJECT_ROOT, "recordings", "20260218 - 1040.mp3")
    PROFILE = REUNIAO_VISATION
    
    print("\n>>> Starting Meeting Profile Flow Test")
    print(f"Profile: {PROFILE.nome}")
    print(f"Audio File: {AUDIO_FILE}")
    print(f"Exists: {os.path.exists(AUDIO_FILE)}")
    
    if not os.path.exists(AUDIO_FILE):
        print("ERROR: Audio file not found. Create a dummy or point to existing.")
        return

    # 1. Transcribe
    print("\n[Step 1] Transcribing...")
    result = None
    start_time = time.time()
    
    try:
        if PROFILE.usar_assemblyai:
            print("Using AssemblyAI...")
            transcriber = AssemblyAITranscriber()
            result = transcriber.transcribe_audio(AUDIO_FILE)
        else:
            print("Using Groq...")
            transcriber = GroqTranscriber()
            result = transcriber.transcribe_audio(AUDIO_FILE)

        print(f"Transcription Complete ({time.time() - start_time:.2f}s)")
        print(f"Status: {result.status}")
        print(f"Length: {len(result.text)} chars")
        
    except Exception as e:
        print(f"TRANSCRIPTION ERROR: {e}")
        return

    save_text_transcript(AUDIO_FILE.replace(".mp3", "_TEST_TRANSCRIPT.mp3"), result)
    save_rich_transcript(AUDIO_FILE.replace(".mp3", "_TEST_TRANSCRIPT.mp3"), result)

    # 2. Generate Report
    report = None
    if PROFILE.gerar_ata:
        print("\n[Step 2] Generating Report (Ata)...")
        try:
            report_gen = ReportGenerator(OpenRouterClient())
            report = report_gen.generate_detailed_report(result)
            print(f"Report Generated: {report.version}")
            save_meeting_report(AUDIO_FILE.replace(".mp3", "_TEST_REPORT.mp3"), report)
            
        except Exception as e:
            print(f"REPORT ERROR: {e}")
            # Continue to telegram test even if report fails? 
            # Usually we need report content. Let's assume report is needed.
            return

    # 3. Telegram
    if PROFILE.enviar_telegram:
        print("\n[Step 3] Sending to Telegram...")
        chat_id = PROFILE.chat_id_telegram
        if not chat_id:
            print("ERROR: No Telegram Chat ID found in profile.")
        else:
            try:
                sender = TelegramSender()
                if sender.available:
                    payload = report.legacy_payload
                    report_str = (
                        "*Contexto e Objetivos*\n"
                        f"{payload.get('contexto_e_objetivos', '')}\n\n"
                        "*Pautas Discutidas*\n"
                        f"{payload.get('pautas_discutidas', '')}\n\n"
                        "*Combinados e Prazos*\n"
                        f"{payload.get('combinados_e_prazos', '')}"
                    )
                    success = sender.send_message(chat_id, report_str)
                    if success:
                        print("Telegram: SUCESSO")
                    else:
                        print("Telegram: FALHA")
                else:
                    print("Telegram Sender Not Available (Check Token)")
            except Exception as e:
                print(f"TELEGRAM ERROR: {e}")

    print("\n>>> Test Completed <<<")

if __name__ == "__main__":
    main()

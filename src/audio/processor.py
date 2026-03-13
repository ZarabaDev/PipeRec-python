"""
PipeRec - FFmpeg Audio Processor
Handles merging, normalization, and export of audio files.
"""

import os
import subprocess
import shutil
from typing import Optional
from datetime import datetime


class AudioProcessor:
    """
    FFmpeg-based audio processor for post-recording operations.
    
    Operations:
    - Merge mic and system audio into stereo (L=mic, R=system)
    - Normalize audio levels using LUFS standard
    - Export to MP3 with configurable bitrate
    """
    
    # Default LUFS target for speech/podcast (Whisper optimized)
    DEFAULT_LUFS = -16
    DEFAULT_TRUE_PEAK = -1.5
    DEFAULT_LRA = 11  # Loudness Range
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize the audio processor.
        
        Args:
            ffmpeg_path: Path to FFmpeg executable (default: system ffmpeg)
        """
        self.ffmpeg_path = ffmpeg_path
        self._verify_ffmpeg()
    
    def _verify_ffmpeg(self):
        """Verify FFmpeg is available."""
        if not shutil.which(self.ffmpeg_path):
            raise RuntimeError(
                f"FFmpeg not found at '{self.ffmpeg_path}'. "
                "Please install FFmpeg: sudo apt install ffmpeg"
            )
    
    def _run_ffmpeg(self, args: list, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run FFmpeg command with arguments."""
        cmd = [self.ffmpeg_path] + args
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True
        )
    
    def merge_to_stereo(
        self,
        mic_wav: str,
        sys_wav: str,
        output_path: str,
        normalize: bool = True,
        target_lufs: float = DEFAULT_LUFS
    ) -> bool:
        """
        Merge mic and system WAV files into a stereo file.
        Mic -> Left channel, System -> Right channel.
        
        Args:
            mic_wav: Path to microphone WAV file
            sys_wav: Path to system WAV file
            output_path: Path for output file
            normalize: Whether to apply LUFS normalization
            target_lufs: Target LUFS level for normalization
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(mic_wav):
            print(f"Error: Mic file not found: {mic_wav}")
            return False
        
        if not os.path.exists(sys_wav):
            print(f"Error: System file not found: {sys_wav}")
            return False
        
        try:
            if normalize:
                # Complex filter: merge to stereo and normalize
                filter_complex = (
                    f"[0:a]pan=mono|c0=c0[l];"
                    f"[1:a]pan=mono|c0=c0[r];"
                    f"[l][r]amerge=inputs=2,"
                    f"loudnorm=I={target_lufs}:TP={self.DEFAULT_TRUE_PEAK}:LRA={self.DEFAULT_LRA}[out]"
                )
            else:
                # Simple merge without normalization
                filter_complex = (
                    f"[0:a]pan=mono|c0=c0[l];"
                    f"[1:a]pan=mono|c0=c0[r];"
                    f"[l][r]amerge=inputs=2[out]"
                )
            
            args = [
                '-y',  # Overwrite output
                '-i', mic_wav,
                '-i', sys_wav,
                '-filter_complex', filter_complex,
                '-map', '[out]',
                output_path
            ]
            
            result = self._run_ffmpeg(args)
            
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error merging audio: {e}")
            return False
    
    def normalize_audio(
        self,
        input_path: str,
        output_path: str,
        target_lufs: float = DEFAULT_LUFS
    ) -> bool:
        """
        Normalize audio to target LUFS level.
        
        Args:
            input_path: Path to input audio file
            output_path: Path for normalized output
            target_lufs: Target LUFS level
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(input_path):
            print(f"Error: Input file not found: {input_path}")
            return False
        
        try:
            args = [
                '-y',
                '-i', input_path,
                '-af', f"loudnorm=I={target_lufs}:TP={self.DEFAULT_TRUE_PEAK}:LRA={self.DEFAULT_LRA}",
                output_path
            ]
            
            result = self._run_ffmpeg(args)
            
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error normalizing audio: {e}")
            return False
    
    def export_mp3(
        self,
        input_path: str,
        output_path: str,
        bitrate: int = 192,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Export audio to MP3 format.
        
        Args:
            input_path: Path to input audio file
            output_path: Path for MP3 output
            bitrate: MP3 bitrate in kbps
            metadata: Optional metadata dict with keys like 'title', 'artist', 'comment'
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(input_path):
            print(f"Error: Input file not found: {input_path}")
            return False
        
        try:
            args = [
                '-y',
                '-i', input_path,
                '-c:a', 'libmp3lame',
                '-b:a', f'{bitrate}k'
            ]
            
            # Add metadata if provided
            if metadata:
                for key, value in metadata.items():
                    args.extend(['-metadata', f'{key}={value}'])
            
            args.append(output_path)
            
            result = self._run_ffmpeg(args)
            
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error exporting MP3: {e}")
            return False
    
    def process_recording(
        self,
        mic_wav: str,
        sys_wav: str,
        output_dir: str,
        filename_prefix: str = "recording",
        normalize: bool = True,
        export_mp3: bool = True,
        keep_wav: bool = False,
        bitrate: int = 192
    ) -> Optional[str]:
        """
        Full processing pipeline: merge, normalize, and export recording.
        
        Args:
            mic_wav: Path to microphone WAV file
            sys_wav: Path to system WAV file
            output_dir: Directory for output files
            filename_prefix: Prefix for output filename
            normalize: Whether to apply LUFS normalization
            export_mp3: Whether to export final as MP3
            keep_wav: Whether to keep intermediate WAV file
            bitrate: MP3 bitrate in kbps
            
        Returns:
            Path to final output file, or None on error
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d - %H%M")
        # User requested specific format "yyyymmaa - hhmm" (assuming dd)
        # We ignore the default "recording" prefix to keep it clean as requested.
        base_name = f"{timestamp}"
        
        # Step 1: Merge to stereo WAV
        merged_wav = os.path.join(output_dir, f"{base_name}_stereo.wav")
        
        print(f"🔀 Merging audio channels...")
        if not self.merge_to_stereo(mic_wav, sys_wav, merged_wav, normalize=normalize):
            return None
        
        # Step 2: Export to MP3 if requested
        if export_mp3:
            output_mp3 = os.path.join(output_dir, f"{base_name}.mp3")
            
            print(f"💾 Exporting to MP3...")
            metadata = {
                'title': f'PipeRec Recording - {timestamp}',
                'artist': 'PipeRec',
                'comment': 'Recorded with PipeRec - Dual capture (L=Mic, R=System)'
            }
            
            if not self.export_mp3(merged_wav, output_mp3, bitrate, metadata):
                return merged_wav  # Return WAV if MP3 fails
            
            # Remove intermediate WAV if not keeping
            if not keep_wav:
                try:
                    os.remove(merged_wav)
                except:
                    pass
            
            return output_mp3
        
        return merged_wav
    
    def cleanup_temp_files(self, *file_paths: str):
        """Remove temporary files."""
        for path in file_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Warning: Could not remove {path}: {e}")

    def cleanup_directory(self, dir_path: str):
        """
        Remove all .wav files in the specified directory.
        Useful for cleaning up temp folder on startup/exit.
        """
        if not os.path.exists(dir_path):
            return
            
        try:
            for filename in os.listdir(dir_path):
                if filename.lower().endswith('.wav'):
                    file_path = os.path.join(dir_path, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            print(f"🧹 Cleaned up: {filename}")
                    except Exception as e:
                        print(f"Warning: Could not remove {file_path}: {e}")
        except Exception as e:
            print(f"Error cleaning directory {dir_path}: {e}")

    def process_for_transcription(
        self,
        mic_wav: str,
        sys_wav: str,
        output_dir: str
    ) -> Optional[str]:
        """
        Process audio specifically for Groq transcription.
        
        Applies:
        - Stereo isolation (Mic=Left, Sys=Right)
        - Volume adjustment (Mic=1.5x)
        - Mixing
        - Speed up (1.2x)
        - Silence removal
        - Downsampling to 16kHz MP3 for small file size
        
        Args:
            mic_wav: Path to mic WAV
            sys_wav: Path to system WAV
            output_dir: Output directory
            
        Returns:
            Path to optimized MP3 file or None
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"transcription_{timestamp}.mp3")
        
        # FFmpeg filter complex string
        # 1. Volume and pan adjustments
        #    Mic: boost volume, put in left channel only (right = silence)
        #    Sys: put in right channel only (left = silence)
        # 2. Mix both stereo streams
        # 3. Tempo up and silence removal
        
        filter_complex = (
            "[0:a]volume=1.5,pan=stereo|c0=c0|c1=0*c0[mic];"
            "[1:a]volume=1.0,pan=stereo|c0=0*c0|c1=c0[sys];"
            "[mic][sys]amix=inputs=2[mix];"
            "[mix]atempo=1.2,silenceremove=start_periods=1:stop_periods=-1:stop_duration=1:stop_threshold=-50dB[out]"
        )
        
        args = [
            '-y',
            '-i', mic_wav,
            '-i', sys_wav,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-ar', '16000',     # 16kHz sample rate
            '-b:a', '48k',      # 48kbps bitrate
            output_path
        ]
        
        print(f"⚡ Processing for transcription (Speedup, Silence Remove, Downsample)...")
        result = self._run_ffmpeg(args)
        
        if result.returncode != 0:
            print(f"FFmpeg processing error: {result.stderr}")
            return None
            
        return output_path

if __name__ == "__main__":
    print("🔧 Testing Audio Processor...")
    
    processor = AudioProcessor()
    print("✅ FFmpeg found and ready!")
    
    # Check FFmpeg version
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
    version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown"
    print(f"   Version: {version_line}")

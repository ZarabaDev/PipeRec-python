"""
PipeRec - Audio Device Detection Module
Detects available input devices using PulseAudio (pactl).
"""

import subprocess
from typing import List, Dict, Optional

def list_pulse_sources() -> List[Dict]:
    """
    List all PulseAudio sources using 'pactl'.
    Returns list of dicts with 'name', 'desc' (if possible), 'type'.
    """
    devices = []
    try:
        # Get machine readable list
        result = subprocess.run(
            ['pactl', 'list', 'sources', 'short'],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return []

        for line in result.stdout.strip().split('\n'):
            parts = line.split('\t')
            if len(parts) >= 2:
                name = parts[1]
                # Simple categorization
                if 'monitor' in name:
                    dtype = 'monitor'
                    clean_name = f"Monitor: {name.split('.')[-2] if '.' in name else name}"
                else:
                    dtype = 'mic'
                    # Try to make a nicer name
                    clean_name = f"Mic: {name.split('.')[-1] if '.' in name else name}"
                
                devices.append({
                    'name': clean_name,
                    'pulse_name': name,
                    'type': dtype,
                    'index': parts[0]
                })

    except Exception as e:
        print(f"Error listing pulse devices: {e}")
        return []
    
    return devices


def list_microphone_devices() -> List[Dict]:
    """List microphone inputs."""
    all_devs = list_pulse_sources()
    return [d for d in all_devs if d['type'] == 'mic']


def list_monitor_devices() -> List[Dict]:
    """List monitor/loopback inputs."""
    all_devs = list_pulse_sources()
    return [d for d in all_devs if d['type'] == 'monitor']

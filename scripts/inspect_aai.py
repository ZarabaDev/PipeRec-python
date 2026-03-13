import assemblyai as aai
import inspect

print("AssemblyAI Version:", aai.__version__)
print("\nTranscriber init signature:")
try:
    print(inspect.signature(aai.Transcriber.__init__))
except:
    print("Could not get init signature")

print("\nTranscribe method signature:")
try:
    print(inspect.signature(aai.Transcriber.transcribe))
except:
    print("Could not get transcribe signature")

print("\nTranscriber dir:")
print([d for d in dir(aai.Transcriber) if not d.startswith('_')])

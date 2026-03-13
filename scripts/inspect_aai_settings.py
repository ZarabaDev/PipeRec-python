import assemblyai as aai

print("AssemblyAI Settings dir:")
print([d for d in dir(aai.settings) if not d.startswith('_')])

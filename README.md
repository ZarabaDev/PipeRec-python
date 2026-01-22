# 🎙️ PipeRec

**Captura Dual de Áudio para Transcrição por IA**

PipeRec é um aplicativo leve para Linux que grava simultaneamente o microfone e o áudio do sistema (loopback), otimizado para transcrição por modelos de IA como Whisper.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Linux-orange)

## ✨ Features

- **Captura Dual**: Grava mic (canal L) e sistema (canal R) simultaneamente
- **Baixo Consumo**: Otimizado para notebooks antigos com buffers grandes
- **Qualidade IA**: Normalização LUFS automática para melhor transcrição
- **Interface Moderna**: GUI com CustomTkinter e tema dark cyberpunk
- **VU Meters**: Monitoramento de níveis em tempo real
- **Global Hotkeys**: `Ctrl+Shift+R` para gravar, `Ctrl+Shift+M` para marker
- **Silent Gate**: Remove silêncio/ruído de fundo do microfone
- **Sistema de Markers**: Timestamps para facilitar revisão

## 🚀 Instalação

### Dependências do Sistema

```bash
# Ubuntu/Pop!_OS/Debian
sudo apt install python3-pip python3-tk ffmpeg libportaudio2 portaudio19-dev \
gir1.2-ayatanaappindicator3-0.1 gir1.2-appindicator3-0.1
```

### Dependências Python

```bash
cd piperec
pip3 install -r requirements.txt --user --break-system-packages
```

## 💻 Uso

### Executar o Aplicativo

```bash
python3 main.py
```

### Atalhos de Teclado Globais

| Atalho | Ação |
|--------|------|
| `Ctrl+Shift+R` | Iniciar/Parar gravação |
| `Ctrl+Shift+M` | Adicionar marker (durante gravação) |

### Fluxo de Trabalho

1. Selecione seu microfone no dropdown
2. Selecione o monitor de sistema (loopback)
3. Clique em **REC** ou pressione `Ctrl+Shift+R`
4. Adicione markers com o botão 📍 ou `Ctrl+Shift+M`
5. Clique em **STOP** para finalizar
6. O arquivo MP3 normalizado será salvo em `recordings/`

## 📁 Estrutura do Projeto

```
piperec/
├── main.py                  # Ponto de entrada
├── requirements.txt         # Dependências Python
├── src/
│   ├── audio/
│   │   ├── capture.py       # Motor de captura dual
│   │   ├── devices.py       # Detecção de dispositivos
│   │   └── processor.py     # FFmpeg wrapper
│   ├── gui/
│   │   ├── app.py           # Janela principal
│   │   ├── components.py    # VU Meter, botões
│   │   └── theme.py         # Cores e estilos
│   └── utils/
│       ├── config.py        # Configurações
│       └── hotkeys.py       # Atalhos globais
├── recordings/              # Arquivos de saída
└── temp/                    # Arquivos temporários
```

## 🔧 Configuração

As configurações são salvas automaticamente em `~/.config/piperec/config.json`:

- Sample rate: 44100 Hz (padrão Whisper)
- Silent gate threshold: -50 dB
- Normalização: -16 LUFS
- Bitrate MP3: 192 kbps

## 🎯 Otimizado para IA

O áudio de saída é especialmente otimizado para transcrição:

- **Canais separados**: Mic no L, Sistema no R
- **Normalização LUFS**: Volume consistente (-16 LUFS)
- **Sample rate**: 44100 Hz (ideal para Whisper)
- **Formato**: MP3 192kbps (bom balanço qualidade/tamanho)

## 📝 Markers

Os markers são salvos em arquivos `.txt` junto com a gravação:

```
# PipeRec - Markers

02:15 - Ponto importante
05:32 - Documento compartilhado
10:45
```

## 🐛 Troubleshooting

### "No module named 'tkinter'"
```bash
sudo apt install python3-tk
```

### "PortAudio library not found"
```bash
sudo apt install libportaudio2 portaudio19-dev
```

### Monitor não detectado
Verifique se o PipeWire está rodando:
```bash
pactl list sources short
```

## 📄 License

MIT License - Use livremente!

---

Feito com ❤️ para gravação de reuniões, chamadas, e transcrição por IA.

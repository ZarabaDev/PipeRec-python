# 🎙️ PipeRec

**Captura Dual de Áudio para Transcrição por IA**

PipeRec é um aplicativo leve para Linux que grava simultaneamente o microfone e o áudio do sistema (via PulseAudio Monitor), otimizado para transcrição por modelos de IA como Whisper.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Linux-orange)

## ✨ Features

- **Captura Dual**: Grava mic (canal L) e sistema (canal R) simultaneamente.
- **Otimizado para IA**: Normalização LUFS automática para melhor precisão na transcrição.
- **Interface Profissional**: GUI estável e responsiva construída com Tkinter.
- **VU Meters**: Monitoramento visual dos níveis de áudio em tempo real.
- **MP3 Otimizado**: Saída direta em MP3 192kbps, 44.1kHz.

## 🚀 Instalação

### Dependências do Sistema

```bash
# Ubuntu/Pop!_OS/Debian
sudo apt install python3-pip python3-tk ffmpeg pulseaudio-utils
```

*Nota: O `pulseaudio-utils` é necessário para o comando `parec`.*

### Dependências Python

```bash
pip3 install -r requirements.txt --user --break-system-packages
```

## 💻 Uso

### Executar o Aplicativo

```bash
python3 main.py
```

### Fluxo de Trabalho

1. **Selecione os Dispositivos**: Escolha seu microfone e o monitor do sistema (loopback) nos menus.
2. **Monitoramento**: Verifique os VU Meters para garantir que o áudio está chegando.
3. **Gravar**: Clique em **REC** para iniciar (o timer começará a contar).
4. **Parar**: Clique em **STOP** para finalizar.
5. **Resultado**: O arquivo processado será salvo automaticamente na pasta `recordings/`.

## 📁 Estrutura do Projeto

```
piperec/
├── main.py                  # Ponto de entrada
├── requirements.txt         # Dependências Python
├── src/
│   ├── audio/
│   │   ├── capture.py       # Motor de captura (parec wrapper)
│   │   ├── devices.py       # Detecção de dispositivos PulseAudio
│   │   └── processor.py     # Processamento FFmpeg (Merge/LUFS/MP3)
│   ├── gui/
│   │   ├── app.py           # Janela principal (Tkinter)
│   │   ├── components.py    # Widgets customizados (VU Meter, Timer)
│   │   └── theme.py         # Constantes de estilo
│   └── utils/
│       └── config.py        # Configurações do usuário
├── recordings/              # Arquivos de saída final
└── temp/                    # Arquivos temporários (wavs brutos)
```

## 🔧 Configuração

As configurações (como últimos dispositivos usados) são salvas automaticamente em `~/.config/piperec/config.json`.

## 🎯 Por que Canais Separados (L/R)?

Modelos de transcrição (como Whisper) funcionam melhor quando as vozes não estão sobrepostas.
- **Canal Esquerdo**: Sua voz (Microfone)
- **Canal Direito**: Áudio do PC (Reunião/Vídeo)

Isso permite separar os locutores (diarização) facilmente no pós-processamento se necessário, ou transcrever o estéreo diretamente com maior clareza.

## 🐛 Troubleshooting

### "FFmpeg not found"
Certifique-se de que o ffmpeg está instalado: `sudo apt install ffmpeg`

### Nenhum dispositivo listado
Verifique se o PulseAudio está rodando. O PipeRec usa comandos nativos do PulseAudio (`pactl`, `parec`).

## 📄 License

MIT License - Use livremente!

---
Feito com ❤️ por ZarabaDev.

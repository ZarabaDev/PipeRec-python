# Flux Audio

Aplicação desktop em Python para captura local de reuniões, transcrição estruturada e geração de artefatos prontos para uso operacional. O projeto nasceu de uma necessidade prática de registrar conversas com separação entre microfone e áudio do sistema, foi adaptado para atender o fluxo atual da Visation e agora evolui na direção de uma base mais genérica, em que cada usuário possa montar localmente seus próprios perfis de gravação e reunião.

## Visão Geral

Hoje o foco do projeto é simples: gravar ou importar áudio, transcrever com provedores externos e salvar artefatos estruturados no disco. A aplicação já carrega o contexto de uso atual da Visation por meio de um perfil dedicado, mas a direção de produto é reduzir acoplamento com fluxos específicos e abrir espaço para perfis configuráveis pelo usuário.

Em termos práticos, isso significa:

- capturar microfone e áudio do sistema em canais separados
- monitorar sinal em tempo real durante a sessão
- processar o áudio final para escuta e para transcrição
- transcrever com `AssemblyAI` ou `Groq`, com fallback configurado por perfil
- exportar texto simples e transcrição rica em JSON
- manter contratos de integração com Visation documentados, mesmo quando não ligados pela interface principal

## Principais Capacidades

- Captura dual local com `parec` via PulseAudio
- Processamento com `ffmpeg` para merge estéreo e exportação em MP3
- Interface desktop em `Tkinter` para uso rápido no dia a dia
- Importação manual de arquivos para transcrição sem precisar gravar
- Perfis de execução para diferentes contextos de reunião
- Transcrição estruturada com segmentos por locutor
- Exportação em `.txt` e `.rich.json`
- Base pronta para evoluir para atas, envio downstream e automações adicionais

## Posicionamento Atual

O projeto já não deve ser lido apenas como um gravador de áudio genérico. Ele se tornou uma ferramenta operacional de apoio a reuniões, inicialmente moldada por um caso real da Visation.

Estado atual:

- o perfil padrão ativo é `Reunião Visation`
- a GUI principal grava, importa, transcreve e salva artefatos locais
- integrações como envio para API da Visation, geração de ata por LLM e Telegram ainda existem no código, mas não fazem parte do fluxo principal exposto na interface

Direção de evolução:

- tornar os perfis menos fixos em código
- permitir criação local de perfis de gravação e reunião
- desacoplar regras específicas de cliente/projeto
- consolidar a aplicação como uma base reutilizável para captura e documentação de reuniões

## Tech Stack

- **Linguagem**: Python 3.10+
- **Interface**: Tkinter
- **Captura de áudio**: PulseAudio (`parec`, `pactl`)
- **Processamento**: FFmpeg
- **Bibliotecas principais**: `numpy`, `Pillow`, `python-dotenv`, `requests`
- **Transcrição**: AssemblyAI e Groq Whisper
- **Geração de relatórios estruturados**: OpenRouter (código disponível, fluxo não exposto na GUI principal)
- **Plataforma alvo atual**: Linux com PulseAudio

## Estrutura do Projeto

```text
flux_audio/
├── main.py
├── requirements.txt
├── README.md
├── .env.example
├── scripts/
│   ├── check_timeout.py
│   ├── inspect_aai.py
│   ├── inspect_aai_settings.py
│   └── test_meeting_flow.py
├── src/
│   ├── audio/
│   │   ├── capture.py
│   │   ├── devices.py
│   │   └── processor.py
│   ├── gui/
│   │   ├── app.py
│   │   ├── components.py
│   │   └── theme.py
│   ├── integrations/
│   │   ├── api_sender.py
│   │   └── telegram_sender.py
│   ├── profiles/
│   │   └── recording_profiles.py
│   ├── transcription/
│   │   ├── assemblyai_client.py
│   │   ├── exporters.py
│   │   ├── groq_client.py
│   │   ├── models.py
│   │   ├── openrouter_client.py
│   │   └── report_generator.py
│   └── utils/
│       └── config.py
└── tests/
    └── test_transcription_exports.py
```

## Como a Aplicação Funciona

### 1. Captura

A aplicação abre dois streams mono com `parec`:

- microfone
- monitor do sistema

Durante a gravação, cada stream é salvo separadamente em WAV temporário.

### 2. Processamento

Ao encerrar a sessão:

- os dois WAVs são combinados em estéreo
- o microfone vai para o canal esquerdo
- o áudio do sistema vai para o canal direito
- o resultado é exportado para MP3 em `recordings/`

Além do arquivo final para escuta, o pipeline também gera uma versão auxiliar para transcrição.

### 3. Transcrição

O provedor é escolhido pelo perfil:

- `AssemblyAI` para transcrição estruturada com diarização
- `Groq` como opção principal em perfis simples ou como fallback

Se o provedor principal falhar e o perfil permitir fallback, a aplicação tenta automaticamente o segundo provedor.

### 4. Exportação

Quando a transcrição termina com sucesso, a aplicação salva:

- `arquivo.txt`: texto com timestamps
- `arquivo.rich.json`: transcrição estruturada com metadata, segmentos e resposta bruta relevante

### 5. Fluxos futuros e auxiliares

O repositório também contém componentes para:

- gerar relatório estruturado de reunião via LLM
- montar payload compatível com a API da Visation
- enviar conteúdo para Telegram

Esses blocos existem para suportar testes, continuidade de integração e futuras evoluções, mas hoje não são o fluxo principal da interface.

## Perfis Disponíveis

Os perfis atuais ficam em [`src/profiles/recording_profiles.py`](/home/zarabatana/Documentos/flux_audio/src/profiles/recording_profiles.py).

### `Gravação Simples`

- foco em captura e transcrição básica
- usa `Groq`
- não gera ata
- não envia para integrações externas

### `Reunião Visation`

- perfil operacional adaptado ao contexto atual da Visation
- usa `AssemblyAI`
- fallback para `Groq`
- mantém lista de participantes esperados
- preserva o caminho para evoluções de relatório e integração downstream

## Pré-requisitos

### Sistema

- Linux
- PulseAudio com acesso a `parec` e `pactl`
- FFmpeg instalado no PATH
- Tkinter disponível no Python do sistema

### Python

- Python 3.10 ou superior
- `pip`

## Instalação

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd flux_audio
```

### 2. Instalar dependências do sistema

Exemplo para Ubuntu, Debian e derivados:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk ffmpeg pulseaudio-utils
```

### 3. Criar ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 5. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Preencha apenas o que fizer sentido para o seu uso local. Nem todas as integrações são obrigatórias para rodar a GUI.

## Variáveis de Ambiente

Use o arquivo [.env.example](/home/zarabatana/Documentos/flux_audio/.env.example) como base.

### Transcrição

| Variável | Obrigatória | Uso |
|---|---:|---|
| `ASSEMBLYAI_API_KEY` | Não | Necessária para perfis que usam AssemblyAI |
| `ASSEMBLYAI_TIMEOUT` | Não | Timeout HTTP da SDK da AssemblyAI |
| `GROQ_API_KEY` | Não | Necessária para perfis que usam Groq |
| `GROQ_TIMEOUT` | Não | Timeout do cliente Groq |

### Relatórios por LLM

| Variável | Obrigatória | Uso |
|---|---:|---|
| `OPENROUTER_API_KEY` | Não | Necessária apenas para fluxos de geração de relatório/ata |

### Integração Visation

| Variável | Obrigatória | Uso |
|---|---:|---|
| `VISATION_API_URL` | Não | Endpoint downstream da Visation |
| `VISATION_API_KEY` | Não | Valor enviado em `X-Internal-Api-Key` |
| `VISATION_INTERNAL_SERVICE` | Não | Valor enviado em `X-Internal-Service` |

### Telegram

| Variável | Obrigatória | Uso |
|---|---:|---|
| `TELEGRAM_BOT_TOKEN` | Não | Necessária apenas para scripts ou fluxos de envio ao Telegram |

## Execução Local

Para iniciar a aplicação desktop:

```bash
python3 main.py
```

## Fluxo de Uso na Interface

1. Abra a aplicação.
2. Escolha o microfone e o monitor do sistema em `Config`.
3. Selecione o perfil de gravação.
4. Inicie a gravação.
5. Encerre a sessão.
6. Aguarde o processamento e a transcrição.
7. Consulte os artefatos gerados localmente.

Também é possível importar um arquivo de áudio diretamente pela interface para executar apenas a etapa de transcrição.

## Saídas Geradas

Por padrão, o projeto trabalha com duas pastas locais:

- `recordings/`: artefatos finais
- `temp/`: arquivos transitórios do pipeline

Arquivos gerados com frequência:

- `YYYYMMDD - HHMM.mp3`
- `YYYYMMDD - HHMM.txt`
- `YYYYMMDD - HHMM.rich.json`

As pastas `recordings/` e `temp/` estão no `.gitignore`.

## Testes

Teste unitário disponível:

```bash
python3 -m unittest tests/test_transcription_exports.py
```

Script de fluxo manual:

```bash
python3 scripts/test_meeting_flow.py
```

O script manual depende de arquivo de áudio real e, conforme o perfil usado, pode exigir chaves de provedores externos.

## Arquitetura por Módulo

### `src/audio`

- `capture.py`: captura concorrente de microfone e sistema
- `devices.py`: descoberta de dispositivos PulseAudio
- `processor.py`: merge, normalização e exportação via FFmpeg

### `src/gui`

- `app.py`: orquestra o fluxo principal da aplicação
- `components.py`: componentes visuais, modal de configuração e painel de progresso
- `theme.py`: tema visual e estilos

### `src/transcription`

- clientes de provedores de transcrição
- modelos de dados tipados para segmentos, metadata e exportação
- utilitários de persistência dos artefatos
- gerador de relatório estruturado baseado em LLM

### `src/profiles`

- perfis de execução atuais
- ponto natural de evolução para suportar perfis definidos pelo usuário

### `src/integrations`

- integrações downstream mantidas no código
- suporte a payload Visation e Telegram

## Limitações Conhecidas

- o alvo atual é Linux com PulseAudio
- os perfis ainda são definidos em código, não pela interface
- a GUI principal hoje não expõe geração de atas nem envio para API/Telegram
- a qualidade da transcrição depende do provedor configurado, do áudio capturado e das chaves válidas
- o perfil `Reunião Visation` ainda carrega contexto específico de operação

## Roadmap de Evolução

- permitir criação e edição local de perfis de gravação e reunião
- desacoplar o conceito de perfil do caso Visation
- expor configurações de exportação e integrações de forma segura
- consolidar relatórios estruturados como etapa opcional e configurável
- ampliar a aplicação para um uso mais genérico sem perder o fluxo operacional já validado

## Troubleshooting

### FFmpeg não encontrado

Instale o pacote do sistema:

```bash
sudo apt install ffmpeg
```

### Nenhum dispositivo listado

Verifique se PulseAudio está ativo e se os dispositivos aparecem em `pactl`.

### Transcrição falha imediatamente

Revise o `.env` e confirme se o perfil ativo está compatível com as chaves configuradas.

### A GUI abre, mas a captura não funciona

Confirme:

- execução em Linux
- presença de `parec`
- acesso ao microfone
- existência de um monitor de saída do sistema

## Licença

MIT.

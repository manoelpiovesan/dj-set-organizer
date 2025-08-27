# I 💖 VIBE CODING





# 🎵 DJ Set Organizer

Um organizador inteligente de sets de DJ com interface gráfica moderna e análise automática de áudio.

## ✨ Funcionalidades

### 🔍 **Análise Automática de Áudio**
- **BPM Detection**: Detecta automaticamente o tempo das músicas
- **Key Detection**: Identifica a nota musical (C, Dm, F#, etc.)
- **Volume Analysis**: Mostra o nível de energia/volume (RMS)
- **Duration**: Duração completa dos arquivos

### 🎧 **Player Integrado**
- Reprodução de MP3 e WAV
- Barra de progresso interativa (estilo SoundCloud)
- Controles Play/Pause/Stop
- Navegação por clique na timeline

### 📋 **Organização Intuitiva**
- **Drag & Drop**: Arraste músicas para reordenar
- **Botões de Controle**: Mover para topo/cima/baixo/final
- **Seleção Simples**: Clique para selecionar, duplo clique para tocar
- **Preview Visual**: Veja todas as informações em uma tabela clara

### 💾 **Export Profissional**
- Copia músicas na ordem desejada
- Renomeia com índice: `01 - Nome da Música.mp3`
- Preserva qualidade original (cópia bit-a-bit)
- Mantém metadados ID3

## 🚀 Instalação

### Requisitos
- Python 3.8+
- Windows/Linux/Mac

### Dependências
```bash
pip install librosa soundfile pygame numpy scipy
```

### Executar
```bash
python main.py
```

## 📖 Como Usar

1. **📁 Selecionar Pasta**: Escolha a pasta com suas músicas
2. **⏳ Aguardar Análise**: O software analisa BPM, notas e volume automaticamente
3. **🎵 Escutar**: Duplo clique nas músicas para preview
4. **📝 Organizar**: Use botões ou drag & drop para reordenar
5. **💾 Exportar**: Clique em "Organizar Set" para salvar na ordem desejada

## 🎯 Interface

```
┌─────────────────────────────────────────────────────────────┐
│ [Selecionar Pasta] Pasta: /Music/TechHouse  [Organizar Set] │
│                                    [↑↑][↑][↓][↓↓]           │
├─────────────────────────────────────────────────────────────┤
│ # │ Nome                    │ BPM │ Nota │ Vol │ Duração    │
│ 1 │ Track Name.mp3          │ 128 │  Am  │ 85% │ 04:32     │
│ 2 │ Another Track.mp3       │ 130 │  C   │ 92% │ 05:15     │
├─────────────────────────────────────────────────────────────┤
│ [▶/⏸] [⏹] Tocando: Track Name.mp3                         │
│ [02:15] ═══════●════════════════════ [04:32]               │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Funcionalidades Técnicas

- **Threading**: Análise em background sem travar a interface
- **Error Handling**: Continua funcionando mesmo com arquivos corrompidos
- **Memory Efficient**: Analisa apenas 1 minuto para detecção, lê metadados para duração
- **Cross-Platform**: Funciona em Windows, Mac e Linux

## ⚠️ Limitações

- **Seek**: pygame tem limitações para pular posições específicas na música
- **Formatos**: Suporta MP3 e WAV (pode ser expandido)
- **Key Detection**: Aproximação baseada em chroma features

## 🎨 Screenshots

*Interface limpa e profissional para organização de sets de DJ*

## 📄 Licença

MIT License - Use livremente para seus sets! 🎶

---

**Criado para DJs que valorizam organização e qualidade** ✨


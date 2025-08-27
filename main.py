import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import threading
import pygame
import librosa
import numpy as np
from pathlib import Path
import re

class DJSetOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizador de Set DJ")
        self.root.geometry("1200x800")
        
        # Variáveis
        self.music_files = []  # Lista de todas as músicas da pasta
        self.set_list = []     # Lista do set organizado
        self.current_playing = None
        self.pygame_initialized = False
        self.music_length = 0
        self.music_position = 0
        self.is_paused = False
        self.position_update_job = None
        
        # Camelot Wheel mapping
        self.camelot_wheel = {
            # Menores (A)
            'Am': '8A', 'Em': '9A', 'Bm': '10A', 'F#m': '11A', 'C#m': '12A', 'G#m': '1A',
            'D#m': '2A', 'A#m': '3A', 'Fm': '4A', 'Cm': '5A', 'Gm': '6A', 'Dm': '7A',
            # Maiores (B)
            'C': '8B', 'G': '9B', 'D': '10B', 'A': '11B', 'E': '12B', 'B': '1B',
            'F#': '2B', 'C#': '3B', 'G#': '4B', 'D#': '5B', 'A#': '6B', 'F': '7B'
        }
        
        # Inicializar pygame mixer
        try:
            pygame.mixer.init()
            self.pygame_initialized = True
        except:
            pass
        
        self.setup_ui()
    
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame superior - controles
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Botão para selecionar pasta
        ttk.Button(control_frame, text="Selecionar Pasta", 
                  command=self.select_folder).pack(side=tk.LEFT, padx=(0, 10))
        
        # Label da pasta selecionada
        self.folder_label = ttk.Label(control_frame, text="Nenhuma pasta selecionada")
        self.folder_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botão para organizar set
        self.organize_btn = ttk.Button(control_frame, text="Exportar Set", 
                                     command=self.organize_set, state=tk.DISABLED)
        self.organize_btn.pack(side=tk.RIGHT)
        
        # Botão para excluir música do set
        self.remove_from_set_btn = ttk.Button(control_frame, text="Excluir do Set", 
                                             command=self.remove_from_set, state=tk.DISABLED)
        self.remove_from_set_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Botão para limpar set
        self.clear_set_btn = ttk.Button(control_frame, text="Limpar Set", 
                                       command=self.clear_set, state=tk.DISABLED)
        self.clear_set_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Frame para botões de reordenação do set
        reorder_frame = ttk.Frame(control_frame)
        reorder_frame.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Label para os botões
        ttk.Label(reorder_frame, text="Reordenar Set:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Botões de reordenação (apenas para o set)
        self.move_top_btn = ttk.Button(reorder_frame, text="⬆⬆", width=4,
                  command=self.move_to_top)
        self.move_top_btn.pack(side=tk.LEFT, padx=(0, 2))
        self.move_up_btn = ttk.Button(reorder_frame, text="⬆", width=4,
                  command=self.move_up)
        self.move_up_btn.pack(side=tk.LEFT, padx=(0, 2))
        self.move_down_btn = ttk.Button(reorder_frame, text="⬇", width=4,
                  command=self.move_down)
        self.move_down_btn.pack(side=tk.LEFT, padx=(0, 2))
        self.move_bottom_btn = ttk.Button(reorder_frame, text="⬇⬇", width=4,
                  command=self.move_to_bottom)
        self.move_bottom_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # Frame principal para as duas listas
        lists_frame = ttk.Frame(main_frame)
        lists_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame da lista de músicas (esquerda)
        music_frame = ttk.LabelFrame(lists_frame, text="📁 Músicas da Pasta")
        music_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Treeview para mostrar todas as músicas
        columns = ('Nome', 'BPM', 'Nota', 'Camelot', 'Volume', 'Duração')
        self.music_tree = ttk.Treeview(music_frame, columns=columns, show='tree headings', height=20)
        
        # Configurar colunas da lista de músicas
        self.music_tree.heading('#0', text='')
        self.music_tree.column('#0', width=0, stretch=False)
        
        for col in columns:
            self.music_tree.heading(col, text=col)
            if col == 'Nome':
                self.music_tree.column(col, width=220, anchor=tk.W)
            elif col == 'BPM':
                self.music_tree.column(col, width=60, anchor=tk.CENTER)
            elif col == 'Nota':
                self.music_tree.column(col, width=50, anchor=tk.CENTER)
            elif col == 'Camelot':
                self.music_tree.column(col, width=60, anchor=tk.CENTER)
            elif col == 'Volume':
                self.music_tree.column(col, width=60, anchor=tk.CENTER)
            elif col == 'Duração':
                self.music_tree.column(col, width=80, anchor=tk.CENTER)
        
        # Scrollbar para a lista de músicas
        music_scrollbar = ttk.Scrollbar(music_frame, orient=tk.VERTICAL, command=self.music_tree.yview)
        self.music_tree.configure(yscrollcommand=music_scrollbar.set)
        
        self.music_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        music_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame central com botões de transferência
        transfer_frame = ttk.Frame(lists_frame)
        transfer_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Espaçador superior
        ttk.Label(transfer_frame, text="").pack(pady=50)
        
        # Botão para adicionar ao set
        self.add_to_set_btn = ttk.Button(transfer_frame, text="➤", width=4,
                                        command=self.add_selected_to_set, state=tk.DISABLED)
        self.add_to_set_btn.pack(pady=5)
        ttk.Label(transfer_frame, text="Adicionar\nao Set", font=("Arial", 8)).pack()
        
        # Espaçador
        ttk.Label(transfer_frame, text="").pack(pady=10)
        
        # Botão para remover do set (alternativo)
        self.remove_from_set_btn2 = ttk.Button(transfer_frame, text="◀", width=4,
                                              command=self.remove_from_set, state=tk.DISABLED)
        self.remove_from_set_btn2.pack(pady=5)
        ttk.Label(transfer_frame, text="Remover\ndo Set", font=("Arial", 8)).pack()
        
        # Espaçador
        ttk.Label(transfer_frame, text="").pack(pady=15)
        
        # Botão para sugestões harmônicas
        self.suggest_btn = ttk.Button(transfer_frame, text="🎵", width=4,
                                     command=self.show_harmonic_suggestions, state=tk.DISABLED)
        self.suggest_btn.pack(pady=5)
        ttk.Label(transfer_frame, text="Sugestões\nHarmônicas", font=("Arial", 8)).pack()
        
        # Frame da lista do set (direita)
        set_frame = ttk.LabelFrame(lists_frame, text="🎵 Set List")
        set_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Treeview para mostrar o set
        set_columns = ('Ordem', 'Nome', 'BPM', 'Nota', 'Camelot', 'Volume', 'Duração')
        self.set_tree = ttk.Treeview(set_frame, columns=set_columns, show='tree headings', height=20)
        
        # Configurar colunas da lista do set
        self.set_tree.heading('#0', text='')
        self.set_tree.column('#0', width=0, stretch=False)
        
        for col in set_columns:
            self.set_tree.heading(col, text=col)
            if col == 'Ordem':
                self.set_tree.column(col, width=50, anchor=tk.CENTER)
            elif col == 'Nome':
                self.set_tree.column(col, width=200, anchor=tk.W)
            elif col == 'BPM':
                self.set_tree.column(col, width=60, anchor=tk.CENTER)
            elif col == 'Nota':
                self.set_tree.column(col, width=50, anchor=tk.CENTER)
            elif col == 'Camelot':
                self.set_tree.column(col, width=60, anchor=tk.CENTER)
            elif col == 'Volume':
                self.set_tree.column(col, width=60, anchor=tk.CENTER)
            elif col == 'Duração':
                self.set_tree.column(col, width=80, anchor=tk.CENTER)
        
        # Scrollbar para a lista do set
        set_scrollbar = ttk.Scrollbar(set_frame, orient=tk.VERTICAL, command=self.set_tree.yview)
        self.set_tree.configure(yscrollcommand=set_scrollbar.set)
        
        self.set_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        set_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind para duplo clique nas duas listas (play música)
        self.music_tree.bind('<Double-1>', self.play_music_from_list)
        self.set_tree.bind('<Double-1>', self.play_music_from_set)
        
        # Bind para seleção na lista de músicas (atualizar botão de adicionar)
        self.music_tree.bind('<ButtonRelease-1>', self.on_music_selection)
        self.music_tree.bind('<KeyRelease>', self.on_music_selection)
        
        # Bind para seleção no set (atualizar botões)
        self.set_tree.bind('<ButtonRelease-1>', self.on_set_selection)
        self.set_tree.bind('<KeyRelease>', self.on_set_selection)
        
        # Bind para drag and drop da lista de músicas para o set
        self.music_tree.bind('<Button-1>', self.on_music_click)
        self.music_tree.bind('<B1-Motion>', self.on_music_drag)
        self.music_tree.bind('<ButtonRelease-1>', self.on_music_drop)
        
        # Bind para reordenar dentro do set
        self.set_tree.bind('<Button-1>', self.on_set_click)
        self.set_tree.bind('<B1-Motion>', self.on_set_drag)
        self.set_tree.bind('<ButtonRelease-1>', self.on_set_drop)
        
        # Frame de controles de áudio
        audio_frame = ttk.Frame(main_frame)
        audio_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Controles de áudio
        ttk.Button(audio_frame, text="Play/Pause", 
                  command=self.toggle_play).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(audio_frame, text="Stop", 
                  command=self.stop_music).pack(side=tk.LEFT, padx=(0, 5))
        
        # Label da música atual
        self.current_music_label = ttk.Label(audio_frame, text="Nenhuma música tocando")
        self.current_music_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Frame da barra de progresso da música
        player_frame = ttk.Frame(main_frame)
        player_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Label do tempo atual
        self.time_current_label = ttk.Label(player_frame, text="00:00")
        self.time_current_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Barra de progresso da música (clicável)
        self.music_progress = ttk.Scale(player_frame, from_=0, to=100, orient=tk.HORIZONTAL)
        self.music_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.music_progress.bind('<Button-1>', self.on_progress_click)
        self.music_progress.bind('<B1-Motion>', self.on_progress_drag)
        
        # Label do tempo total
        self.time_total_label = ttk.Label(player_frame, text="00:00")
        self.time_total_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Barra de progresso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_label = ttk.Label(progress_frame, text="Carregando músicas...")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        self.progress_bar.pack_forget()  # Esconder inicialmente
        
        # Variáveis para drag and drop
        self.drag_data = {'item': None, 'index': None, 'dragging': False, 'source': None}
        
        # Atualizar estado inicial dos botões
        self.update_buttons()
        self.update_transfer_buttons()
    
    def select_folder(self):
        folder = filedialog.askdirectory(title="Selecionar pasta com músicas")
        if folder:
            self.folder_label.config(text=f"Pasta: {folder}")
            self.load_music_files(folder)
    
    def load_music_files(self, folder):
        self.progress_label.config(text="Carregando músicas...")
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        self.progress_bar['value'] = 0
        
        # Executar em thread separada para não travar a interface
        thread = threading.Thread(target=self._load_files_thread, args=(folder,))
        thread.daemon = True
        thread.start()
    
    def _load_files_thread(self, folder):
        # Encontrar arquivos de música
        music_extensions = ['.mp3', '.wav']
        files = []
        
        for ext in music_extensions:
            files.extend(Path(folder).glob(f'**/*{ext}'))
            files.extend(Path(folder).glob(f'**/*{ext.upper()}'))
        
        self.music_files = []
        total_files = len(files)
        
        for i, file_path in enumerate(files):
            try:
                # Analisar arquivo de áudio
                music_info = self.analyze_audio(str(file_path))
                if music_info:
                    self.music_files.append(music_info)
                
                # Atualizar progresso na thread principal
                progress = (i + 1) / total_files * 100
                self.root.after(0, self.update_progress, progress)
                
            except Exception as e:
                print(f"Erro crítico ao processar {file_path}: {e}")
                # Adicionar arquivo básico mesmo com erro
                basic_info = {
                    'path': str(file_path),
                    'name': Path(file_path).name,
                    'bpm': 120,
                    'key': "N/A",
                    'camelot': "N/A",
                    'volume': "N/A",
                    'duration': "N/A"
                }
                self.music_files.append(basic_info)
        
        # Atualizar interface na thread principal
        self.root.after(0, self.update_music_list)
    
    def analyze_audio(self, file_path):
        try:
            # Carregar áudio
            y, sr = librosa.load(file_path, duration=60)  # Analisar apenas primeiro minuto
            
            # Calcular BPM
            try:
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                # Garantir que extraímos um escalar do array
                if hasattr(tempo, 'item'):
                    bpm = int(tempo.item())
                else:
                    bpm = int(tempo)
            except:
                bpm = 120  # BPM padrão se não conseguir detectar
            
            # Estimar nota (chroma features)
            try:
                chroma = librosa.feature.chroma_stft(y=y, sr=sr)
                chroma_mean = np.mean(chroma, axis=1)
                note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                dominant_note = note_names[np.argmax(chroma_mean)]
                
                # Detectar se é maior ou menor (aproximação simples)
                # Verificar se há predominância de acordes menores
                minor_indicator = chroma_mean[3] + chroma_mean[7] + chroma_mean[10]  # acordes menores
                major_indicator = chroma_mean[0] + chroma_mean[4] + chroma_mean[7]   # acordes maiores
                
                if minor_indicator > major_indicator:
                    key = f"{dominant_note}m"
                else:
                    key = dominant_note
            except:
                key = "N/A"  # Se não conseguir detectar a nota
            
            # Calcular volume (RMS - Root Mean Square)
            try:
                rms = librosa.feature.rms(y=y)[0]
                avg_rms = np.mean(rms)
                # Converter para decibéis e normalizar para uma escala mais legível
                volume_db = 20 * np.log10(avg_rms + 1e-6)  # +1e-6 para evitar log(0)
                # Normalizar para escala de 0-100 (aproximada)
                volume_normalized = max(0, min(100, int((volume_db + 60) * 100 / 60)))
                volume_str = f"{volume_normalized}%"
            except:
                volume_str = "N/A"
            
            # Duração (do arquivo completo, não do trecho analisado)
            try:
                duration = librosa.get_duration(path=file_path)
                duration_str = f"{int(duration//60):02d}:{int(duration%60):02d}"
            except:
                duration_str = "00:00"
            
            return {
                'path': file_path,
                'name': Path(file_path).name,
                'bpm': bpm,
                'key': key,
                'camelot': self.get_camelot_code(key),
                'volume': volume_str,
                'duration': duration_str
            }
            
        except Exception as e:
            print(f"Erro ao analisar {file_path}: {e}")
            # Retornar informações básicas mesmo se a análise falhar
            return {
                'path': file_path,
                'name': Path(file_path).name,
                'bpm': 120,
                'key': "N/A",
                'camelot': "N/A",
                'volume': "N/A",
                'duration': "N/A"
            }
    
    def update_progress(self, value):
        self.progress_bar['value'] = value
        self.root.update_idletasks()
    
    def update_music_list(self):
        # Limpar lista de músicas
        for item in self.music_tree.get_children():
            self.music_tree.delete(item)
        
        # Adicionar todas as músicas na lista da esquerda
        for music in self.music_files:
            self.music_tree.insert('', 'end', values=(
                music['name'], music['bpm'], music['key'], music['camelot'], music['volume'], music['duration']
            ))
        
        self.progress_bar.pack_forget()
        self.progress_label.config(text=f"{len(self.music_files)} músicas carregadas")
        self.organize_btn.config(state=tk.NORMAL)
        self.clear_set_btn.config(state=tk.NORMAL)
    
    def update_set_list(self):
        # Limpar lista do set
        for item in self.set_tree.get_children():
            self.set_tree.delete(item)
        
        # Adicionar músicas do set na lista da direita
        for i, music in enumerate(self.set_list, 1):
            self.set_tree.insert('', 'end', values=(
                i, music['name'], music['bpm'], music['key'], music['camelot'], music['volume'], music['duration']
            ))
    
    def play_music_from_list(self, event):
        """Toca música da lista de músicas (esquerda)"""
        selection = self.music_tree.selection()
        if selection:
            item = selection[0]
            values = self.music_tree.item(item, 'values')
            if values:
                # Encontrar música pelo nome
                music_name = values[0]
                for music in self.music_files:
                    if music['name'] == music_name:
                        self.play_selected_music(music)
                        break
    
    def play_music_from_set(self, event):
        """Toca música da lista do set (direita)"""
        selection = self.set_tree.selection()
        if selection:
            item = selection[0]
            values = self.set_tree.item(item, 'values')
            if values:
                # Encontrar música pelo nome
                music_name = values[1]  # Nome está na segunda coluna (após ordem)
                for music in self.set_list:
                    if music['name'] == music_name:
                        self.play_selected_music(music)
                        break
    
    def play_selected_music(self, music):
        """Toca uma música específica"""
        if not self.pygame_initialized:
            messagebox.showerror("Erro", "Sistema de áudio não inicializado")
            return
        
        try:
            pygame.mixer.music.load(music['path'])
            pygame.mixer.music.play()
            self.current_playing = music['path']
            
            # Obter duração da música
            duration_str = music['duration']
            if duration_str != "N/A":
                parts = duration_str.split(':')
                self.music_length = int(parts[0]) * 60 + int(parts[1])
            else:
                self.music_length = 0
            
            # Configurar barra de progresso
            self.music_progress.config(to=self.music_length)
            self.time_total_label.config(text=duration_str)
            self.music_position = 0
            self.is_paused = False
            
            # Atualizar labels
            self.current_music_label.config(text=f"Tocando: {music['name']}")
            self.time_current_label.config(text="00:00")
            
            # Iniciar atualização da posição
            self.start_position_update()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível tocar a música: {e}")
    
    def toggle_play(self):
        if not self.pygame_initialized:
            return
            
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.current_music_label.config(text="Pausado")
                self.is_paused = True
                self.stop_position_update()
            else:
                pygame.mixer.music.unpause()
                if self.current_playing:
                    name = Path(self.current_playing).name
                    self.current_music_label.config(text=f"Tocando: {name}")
                    self.is_paused = False
                    self.start_position_update()
        except:
            pass
    
    def stop_music(self):
        if not self.pygame_initialized:
            return
            
        try:
            pygame.mixer.music.stop()
            self.current_playing = None
            self.current_music_label.config(text="Parado")
            self.music_position = 0
            self.is_paused = False
            self.music_progress.set(0)
            self.time_current_label.config(text="00:00")
            self.stop_position_update()
        except:
            pass
    
    def on_music_click(self, event):
        """Clique na lista de músicas"""
        item = self.music_tree.selection()[0] if self.music_tree.selection() else None
        if item:
            self.drag_data = {
                'item': item,
                'index': self.music_tree.index(item),
                'start_x': event.x,
                'start_y': event.y,
                'dragging': False,
                'source': 'music'
            }
    
    def on_music_drag(self, event):
        """Arrastar da lista de músicas"""
        if self.drag_data.get('item') and not self.drag_data.get('dragging'):
            start_x = self.drag_data.get('start_x', 0)
            start_y = self.drag_data.get('start_y', 0)
            
            if abs(event.x - start_x) > 10 or abs(event.y - start_y) > 10:
                self.drag_data['dragging'] = True
    
    def on_music_drop(self, event):
        """Drop da música no set"""
        if self.drag_data.get('item') and self.drag_data.get('dragging'):
            # Verificar se foi solto na área do set
            try:
                # Obter coordenadas do widget do set
                set_x = self.set_tree.winfo_rootx()
                set_y = self.set_tree.winfo_rooty()
                set_width = self.set_tree.winfo_width()
                set_height = self.set_tree.winfo_height()
                
                # Coordenadas do mouse na tela
                mouse_x = event.x_root
                mouse_y = event.y_root
                
                # Verificar se está dentro da área do set
                if (set_x <= mouse_x <= set_x + set_width and 
                    set_y <= mouse_y <= set_y + set_height):
                    
                    # Adicionar música ao set
                    values = self.music_tree.item(self.drag_data['item'], 'values')
                    music_name = values[0]
                    
                    # Encontrar a música completa
                    for music in self.music_files:
                        if music['name'] == music_name:
                            self.set_list.append(music.copy())
                            self.update_set_list()
                            break
                            
            except Exception as e:
                print(f"Erro no drag and drop: {e}")
        
        # Limpar dados de drag
        self.drag_data = {'item': None, 'index': None, 'dragging': False, 'source': None}
        
        # Atualizar botões após o drop
        self.update_transfer_buttons()
    
    def on_set_click(self, event):
        """Clique na lista do set"""
        item = self.set_tree.selection()[0] if self.set_tree.selection() else None
        if item:
            self.drag_data = {
                'item': item,
                'index': self.set_tree.index(item),
                'start_x': event.x,
                'start_y': event.y,
                'dragging': False,
                'source': 'set'
            }
    
    def on_set_drag(self, event):
        """Arrastar dentro do set"""
        if self.drag_data.get('item') and not self.drag_data.get('dragging'):
            start_x = self.drag_data.get('start_x', 0)
            start_y = self.drag_data.get('start_y', 0)
            
            if abs(event.x - start_x) > 10 or abs(event.y - start_y) > 10:
                self.drag_data['dragging'] = True
    
    def on_set_drop(self, event):
        """Drop para reordenar dentro do set"""
        if self.drag_data.get('item') and self.drag_data.get('dragging') and self.drag_data.get('source') == 'set':
            target = self.set_tree.identify_row(event.y)
            if target and target != self.drag_data['item']:
                # Reordenar dentro do set
                old_index = self.drag_data['index']
                target_index = self.set_tree.index(target)
                
                # Mover na lista interna
                music_item = self.set_list.pop(old_index)
                self.set_list.insert(target_index, music_item)
                
                # Atualizar interface
                self.update_set_list()
                
                # Reselecionar item movido
                new_item = self.set_tree.get_children()[target_index]
                self.set_tree.selection_set(new_item)
                self.set_tree.focus(new_item)
        
        # Limpar dados de drag
        self.drag_data = {'item': None, 'index': None, 'dragging': False, 'source': None}
        
        # Atualizar botões após o drop
        self.update_buttons()
        self.update_transfer_buttons()
    
    def update_order_numbers(self):
        """Atualiza números de ordem no set"""
        for i, item in enumerate(self.set_tree.get_children()):
            values = list(self.set_tree.item(item, 'values'))
            values[0] = str(i + 1)  # Atualizar número da ordem
            self.set_tree.item(item, values=values)
    
    def clear_set(self):
        """Limpa a lista do set"""
        self.set_list.clear()
        self.update_set_list()
        self.update_buttons()
        self.update_transfer_buttons()
    
    def organize_set(self):
        if not self.set_list:
            messagebox.showwarning("Aviso", "Nenhuma música no set")
            return
        
        # Selecionar pasta de destino
        dest_folder = filedialog.askdirectory(title="Selecionar pasta para salvar o set organizado")
        if not dest_folder:
            return
        
        try:
            # Criar pasta se não existir
            os.makedirs(dest_folder, exist_ok=True)
            
            # Copiar arquivos na ordem do set
            for i, music in enumerate(self.set_list, 1):
                source_path = music['path']
                extension = Path(source_path).suffix
                new_name = f"{i:02d} - {music['name']}"
                dest_path = os.path.join(dest_folder, new_name)
                
                shutil.copy2(source_path, dest_path)
            
            messagebox.showinfo("Sucesso", 
                              f"Set exportado com sucesso!\n{len(self.set_list)} músicas copiadas para:\n{dest_folder}")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar set: {e}")

    def get_selected_index(self):
        """Retorna o índice da música selecionada no set ou None se nenhuma estiver selecionada"""
        selection = self.set_tree.selection()
        if selection:
            item = selection[0]
            values = self.set_tree.item(item, 'values')
            if values:
                return int(values[0]) - 1  # Converter para índice 0-based
        return None
    
    def move_to_top(self):
        """Move a música selecionada para o topo do set"""
        index = self.get_selected_index()
        if index is None or index == 0 or not self.set_list:
            return  # Nada selecionado ou já está no topo
        
        # Mover na lista interna
        music_item = self.set_list.pop(index)
        self.set_list.insert(0, music_item)
        
        # Atualizar interface
        self.update_set_list()
        self.update_buttons()
        
        # Reselecionar o item na nova posição
        first_item = self.set_tree.get_children()[0]
        self.set_tree.selection_set(first_item)
        self.set_tree.focus(first_item)
        self.update_buttons()
    
    def move_up(self):
        """Move a música selecionada uma posição para cima no set"""
        index = self.get_selected_index()
        if index is None or index == 0 or not self.set_list:
            return  # Nada selecionado ou já está no topo
        
        # Trocar posições na lista interna
        self.set_list[index], self.set_list[index-1] = self.set_list[index-1], self.set_list[index]
        
        # Atualizar interface
        self.update_set_list()
        self.update_buttons()
        
        # Reselecionar o item na nova posição
        new_item = self.set_tree.get_children()[index-1]
        self.set_tree.selection_set(new_item)
        self.set_tree.focus(new_item)
        self.update_buttons()
    
    def move_down(self):
        """Move a música selecionada uma posição para baixo no set"""
        index = self.get_selected_index()
        if index is None or index >= len(self.set_list) - 1 or not self.set_list:
            return  # Nada selecionado ou já está no final
        
        # Trocar posições na lista interna
        self.set_list[index], self.set_list[index+1] = self.set_list[index+1], self.set_list[index]
        
        # Atualizar interface
        self.update_set_list()
        self.update_buttons()
        
        # Reselecionar o item na nova posição
        new_item = self.set_tree.get_children()[index+1]
        self.set_tree.selection_set(new_item)
        self.set_tree.focus(new_item)
        self.update_buttons()
    
    def move_to_bottom(self):
        """Move a música selecionada para o final do set"""
        index = self.get_selected_index()
        if index is None or index >= len(self.set_list) - 1 or not self.set_list:
            return  # Nada selecionado ou já está no final
        
        # Mover na lista interna
        music_item = self.set_list.pop(index)
        self.set_list.append(music_item)
        
        # Atualizar interface
        self.update_set_list()
        self.update_buttons()
        
        # Reselecionar o item na nova posição
        last_item = self.set_tree.get_children()[-1]
        self.set_tree.selection_set(last_item)
        self.set_tree.focus(last_item)
        self.update_buttons()

    def start_position_update(self):
        """Inicia a atualização da posição da música"""
        self.stop_position_update()  # Para qualquer atualização anterior
        self.update_position()
    
    def stop_position_update(self):
        """Para a atualização da posição da música"""
        if self.position_update_job:
            self.root.after_cancel(self.position_update_job)
            self.position_update_job = None
    
    def update_position(self):
        """Atualiza a posição da barra de progresso"""
        if self.current_playing and not self.is_paused and pygame.mixer.music.get_busy():
            # Incrementar posição (aproximação, já que pygame não fornece posição real)
            self.music_position += 1
            
            # Atualizar barra de progresso
            if self.music_length > 0:
                self.music_progress.set(self.music_position)
            
            # Atualizar label do tempo atual
            minutes = self.music_position // 60
            seconds = self.music_position % 60
            self.time_current_label.config(text=f"{minutes:02d}:{seconds:02d}")
            
            # Verificar se música terminou
            if self.music_position >= self.music_length:
                self.stop_music()
                return
            
            # Agendar próxima atualização
            self.position_update_job = self.root.after(1000, self.update_position)
    
    def on_progress_click(self, event):
        """Manipula clique na barra de progresso"""
        if self.current_playing and self.music_length > 0:
            # Calcular nova posição baseada no clique
            widget_width = self.music_progress.winfo_width()
            click_x = event.x
            new_position = int((click_x / widget_width) * self.music_length)
            
            # Definir nova posição
            self.set_music_position(new_position)
    
    def on_progress_drag(self, event):
        """Manipula arrastar na barra de progresso"""
        self.on_progress_click(event)  # Mesmo comportamento que clique
    
    def set_music_position(self, position):
        """Define uma nova posição na música"""
        if self.current_playing and self.music_length > 0:
            # Limitar posição aos limites da música
            position = max(0, min(position, self.music_length))
            
            # Infelizmente, pygame não suporta seek diretamente
            # Vamos simular recarregando e "pulando" o tempo
            # Nota: Esta é uma limitação do pygame - para seek real, 
            # seria necessário usar outras bibliotecas como python-vlc
            
            self.music_position = position
            self.music_progress.set(position)
            
            # Atualizar label do tempo
            minutes = position // 60
            seconds = position % 60
            self.time_current_label.config(text=f"{minutes:02d}:{seconds:02d}")
            
            # Mostrar aviso sobre limitação
            if position != self.music_position:
                messagebox.showinfo("Aviso", 
                    "Função de pular para posição específica tem limitações com pygame.\n"
                    "Para melhor controle, considere usar um player mais avançado.")

    def remove_from_set(self):
        """Remove música selecionada do set."""
        selected_items = self.set_tree.selection()
        if selected_items:
            for item in selected_items:
                # Obter índice da música selecionada
                values = self.set_tree.item(item, 'values')
                if values:
                    ordem = int(values[0]) - 1  # Converter para índice 0-based
                    # Remover da lista interna
                    if 0 <= ordem < len(self.set_list):
                        del self.set_list[ordem]
            
            # Atualizar lista do set
            self.update_set_list()
            self.update_buttons()
            self.update_transfer_buttons()

    def update_buttons(self):
        """Atualiza estado dos botões conforme seleção."""
        selected_items = self.set_tree.selection()
        has_selection = len(selected_items) > 0
        has_set_items = len(self.set_list) > 0
        
        # Botões de reordenação
        self.move_top_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.move_up_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.move_down_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.move_bottom_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        
        # Botão de excluir do set
        self.remove_from_set_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.remove_from_set_btn2.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        
        # Botão de limpar set
        self.clear_set_btn.config(state=tk.NORMAL if has_set_items else tk.DISABLED)
        
        # Botão de exportar set
        self.organize_btn.config(state=tk.NORMAL if has_set_items else tk.DISABLED)
    
    def add_selected_to_set(self):
        """Adiciona música selecionada da lista de músicas para o set."""
        selected_items = self.music_tree.selection()
        if selected_items:
            for item in selected_items:
                values = self.music_tree.item(item, 'values')
                if values:
                    music_name = values[0]
                    
                    # Encontrar a música completa
                    for music in self.music_files:
                        if music['name'] == music_name:
                            # Verificar se já está no set
                            already_in_set = any(set_music['name'] == music_name for set_music in self.set_list)
                            if not already_in_set:
                                self.set_list.append(music.copy())
                            break
            
            # Atualizar lista do set
            self.update_set_list()
            self.update_buttons()
            
            # Limpar seleção da lista de músicas
            self.music_tree.selection_remove(self.music_tree.selection())
            self.update_transfer_buttons()

    def update_transfer_buttons(self):
        """Atualiza estado dos botões de transferência conforme seleção."""
        music_selected = len(self.music_tree.selection()) > 0
        set_selected = len(self.set_tree.selection()) > 0
        has_set_items = len(self.set_list) > 0
        
        # Botão de adicionar ao set
        self.add_to_set_btn.config(state=tk.NORMAL if music_selected else tk.DISABLED)
        
        # Botão alternativo de remover do set
        self.remove_from_set_btn2.config(state=tk.NORMAL if set_selected else tk.DISABLED)
        
        # Botão de sugestões harmônicas
        self.suggest_btn.config(state=tk.NORMAL if set_selected else tk.DISABLED)

    def on_music_selection(self, event):
        """Manipula seleção na lista de músicas"""
        # Só atualizar se não estiver arrastando
        if not self.drag_data.get('dragging', False):
            self.update_transfer_buttons()
    
    def on_set_selection(self, event):
        """Manipula seleção na lista do set"""
        # Só atualizar se não estiver arrastando
        if not self.drag_data.get('dragging', False):
            self.update_buttons()
            self.update_transfer_buttons()
            # Destacar músicas compatíveis
            self.root.after(100, self.highlight_compatible_tracks)
    
    def get_camelot_code(self, key):
        """Converte uma nota musical para código Camelot"""
        if key in self.camelot_wheel:
            return self.camelot_wheel[key]
        return "N/A"
    
    def get_compatible_keys(self, camelot_code):
        """Retorna as chaves compatíveis para mixagem harmônica"""
        if camelot_code == "N/A":
            return []
        
        try:
            # Extrair número e letra
            number = int(camelot_code[:-1])
            letter = camelot_code[-1]
            
            compatible = []
            
            # Regras do Camelot Wheel:
            # 1. Mesma chave (perfeita)
            compatible.append(camelot_code)
            
            # 2. +1/-1 no círculo (mesmo modo)
            next_num = (number % 12) + 1
            prev_num = ((number - 2) % 12) + 1
            compatible.append(f"{next_num}{letter}")
            compatible.append(f"{prev_num}{letter}")
            
            # 3. Modo relativo (mesmo número, letra oposta)
            opposite_letter = 'B' if letter == 'A' else 'A'
            compatible.append(f"{number}{opposite_letter}")
            
            # 4. +1/-1 do modo relativo
            compatible.append(f"{next_num}{opposite_letter}")
            compatible.append(f"{prev_num}{opposite_letter}")
            
            return compatible
            
        except:
            return []
    
    def calculate_mixing_compatibility(self, key1, key2):
        """Calcula compatibilidade entre duas chaves (0-100%)"""
        camelot1 = self.get_camelot_code(key1)
        camelot2 = self.get_camelot_code(key2)
        
        if camelot1 == "N/A" or camelot2 == "N/A":
            return 0
        
        if camelot1 == camelot2:
            return 100  # Perfeita
        
        compatible_keys = self.get_compatible_keys(camelot1)
        
        if camelot2 in compatible_keys:
            # Determinar tipo de compatibilidade
            try:
                num1 = int(camelot1[:-1])
                letter1 = camelot1[-1]
                num2 = int(camelot2[:-1])
                letter2 = camelot2[-1]
                
                if letter1 == letter2:  # Mesmo modo
                    return 90
                elif num1 == num2:  # Modo relativo
                    return 85
                else:  # +1/-1 do relativo
                    return 75
            except:
                return 50
        
        return 25  # Compatibilidade baixa

    def show_harmonic_suggestions(self):
        """Mostra sugestões harmônicas baseadas na música selecionada no set"""
        selection = self.set_tree.selection()
        if not selection:
            messagebox.showinfo("Aviso", "Selecione uma música no set para ver sugestões harmônicas")
            return
        
        # Obter música selecionada
        item = selection[0]
        values = self.set_tree.item(item, 'values')
        if not values:
            return
        
        selected_music_name = values[1]  # Nome está na segunda coluna
        selected_music = None
        
        for music in self.set_list:
            if music['name'] == selected_music_name:
                selected_music = music
                break
        
        if not selected_music:
            return
        
        # Encontrar sugestões
        suggestions = self.find_harmonic_matches(selected_music)
        
        if not suggestions:
            messagebox.showinfo("Sugestões Harmônicas", 
                              f"Nenhuma sugestão harmônica encontrada para:\n{selected_music['name']}")
            return
        
        # Criar janela de sugestões
        self.create_suggestions_window(selected_music, suggestions)
    
    def find_harmonic_matches(self, reference_music):
        """Encontra músicas compatíveis harmonicamente"""
        suggestions = []
        reference_camelot = reference_music['camelot']
        reference_bpm = reference_music['bpm']
        
        if reference_camelot == "N/A":
            return suggestions
        
        compatible_keys = self.get_compatible_keys(reference_camelot)
        
        for music in self.music_files:
            # Não sugerir a própria música ou músicas já no set
            if music['name'] == reference_music['name']:
                continue
            
            already_in_set = any(set_music['name'] == music['name'] for set_music in self.set_list)
            if already_in_set:
                continue
            
            # Calcular compatibilidade
            harmonic_score = self.calculate_mixing_compatibility(reference_music['key'], music['key'])
            
            # Calcular compatibilidade de BPM (diferença máxima de 6 BPM é considerada boa)
            bpm_diff = abs(reference_bpm - music['bpm'])
            if bpm_diff <= 3:
                bpm_score = 100
            elif bpm_diff <= 6:
                bpm_score = 80
            elif bpm_diff <= 10:
                bpm_score = 60
            else:
                bpm_score = max(0, 60 - (bpm_diff - 10) * 2)
            
            # Score total (70% harmônico, 30% BPM)
            total_score = (harmonic_score * 0.7) + (bpm_score * 0.3)
            
            if total_score >= 50:  # Só mostrar sugestões com score razoável
                suggestions.append({
                    'music': music,
                    'harmonic_score': harmonic_score,
                    'bpm_score': bpm_score,
                    'total_score': total_score,
                    'bpm_diff': bpm_diff
                })
        
        # Ordenar por score total
        suggestions.sort(key=lambda x: x['total_score'], reverse=True)
        return suggestions[:10]  # Limitar a 10 sugestões
    
    def create_suggestions_window(self, reference_music, suggestions):
        """Cria janela com sugestões harmônicas"""
        window = tk.Toplevel(self.root)
        window.title("Sugestões Harmônicas")
        window.geometry("800x500")
        window.transient(self.root)
        window.grab_set()
        
        # Header
        header_frame = ttk.Frame(window)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header_frame, text="Sugestões harmônicas para:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text=f"{reference_music['name']} - {reference_music['key']} ({reference_music['camelot']}) - {reference_music['bpm']} BPM", 
                 font=("Arial", 10)).pack(anchor=tk.W)
        
        # Lista de sugestões
        suggestions_frame = ttk.Frame(window)
        suggestions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('Nome', 'Nota', 'Camelot', 'BPM', 'Δ BPM', 'Score Harmônico', 'Score Total')
        suggestions_tree = ttk.Treeview(suggestions_frame, columns=columns, show='tree headings', height=15)
        
        # Configurar colunas
        suggestions_tree.heading('#0', text='')
        suggestions_tree.column('#0', width=0, stretch=False)
        
        for col in columns:
            suggestions_tree.heading(col, text=col)
            if col == 'Nome':
                suggestions_tree.column(col, width=250, anchor=tk.W)
            elif col in ['Nota', 'Camelot']:
                suggestions_tree.column(col, width=60, anchor=tk.CENTER)
            elif col in ['BPM', 'Δ BPM']:
                suggestions_tree.column(col, width=60, anchor=tk.CENTER)
            else:
                suggestions_tree.column(col, width=80, anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(suggestions_frame, orient=tk.VERTICAL, command=suggestions_tree.yview)
        suggestions_tree.configure(yscrollcommand=scrollbar.set)
        
        suggestions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Adicionar sugestões
        for suggestion in suggestions:
            music = suggestion['music']
            suggestions_tree.insert('', 'end', values=(
                music['name'],
                music['key'],
                music['camelot'],
                music['bpm'],
                f"+{suggestion['bpm_diff']}" if suggestion['bpm_diff'] >= 0 else str(suggestion['bpm_diff']),
                f"{suggestion['harmonic_score']:.0f}%",
                f"{suggestion['total_score']:.0f}%"
            ))
        
        # Botões
        button_frame = ttk.Frame(window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def add_suggestion():
            selected = suggestions_tree.selection()
            if selected:
                item = selected[0]
                values = suggestions_tree.item(item, 'values')
                music_name = values[0]
                
                # Encontrar música e adicionar ao set
                for suggestion in suggestions:
                    if suggestion['music']['name'] == music_name:
                        self.set_list.append(suggestion['music'].copy())
                        self.update_set_list()
                        self.update_buttons()
                        window.destroy()
                        break
        
        ttk.Button(button_frame, text="Adicionar ao Set", command=add_suggestion).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Fechar", command=window.destroy).pack(side=tk.RIGHT)
        
        # Bind duplo clique
        suggestions_tree.bind('<Double-1>', lambda e: add_suggestion())
    
    def highlight_compatible_tracks(self):
        """Destaca músicas compatíveis com a seleção atual do set"""
        # Limpar destaque anterior
        for item in self.music_tree.get_children():
            self.music_tree.set(item, 'tags', '')
        
        selection = self.set_tree.selection()
        if not selection:
            return
        
        # Obter música selecionada no set
        item = selection[0]
        values = self.set_tree.item(item, 'values')
        if not values:
            return
        
        selected_music_name = values[1]
        selected_music = None
        
        for music in self.set_list:
            if music['name'] == selected_music_name:
                selected_music = music
                break
        
        if not selected_music or selected_music['camelot'] == "N/A":
            return
        
        # Configurar tags de cores
        self.music_tree.tag_configure('perfect', background='#90EE90')  # Verde claro
        self.music_tree.tag_configure('good', background='#FFFFE0')     # Amarelo claro  
        self.music_tree.tag_configure('ok', background='#FFE4E1')       # Rosa claro
        
        # Destacar músicas compatíveis
        for music_item in self.music_tree.get_children():
            music_values = self.music_tree.item(music_item, 'values')
            music_name = music_values[0]
            
            # Encontrar música completa
            for music in self.music_files:
                if music['name'] == music_name:
                    compatibility = self.calculate_mixing_compatibility(selected_music['key'], music['key'])
                    
                    if compatibility >= 90:
                        self.music_tree.item(music_item, tags='perfect')
                    elif compatibility >= 75:
                        self.music_tree.item(music_item, tags='good')
                    elif compatibility >= 50:
                        self.music_tree.item(music_item, tags='ok')
                    
                    break

def main():
    root = tk.Tk()
    app = DJSetOrganizer(root)
    root.mainloop()

if __name__ == "__main__":
    main()

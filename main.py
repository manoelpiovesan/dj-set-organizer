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
        self.music_files = []
        self.current_playing = None
        self.pygame_initialized = False
        self.music_length = 0
        self.music_position = 0
        self.is_paused = False
        self.position_update_job = None
        
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
        self.organize_btn = ttk.Button(control_frame, text="Organizar Set", 
                                     command=self.organize_set, state=tk.DISABLED)
        self.organize_btn.pack(side=tk.RIGHT)
        
        # Frame para botões de reordenação
        reorder_frame = ttk.Frame(control_frame)
        reorder_frame.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Botões de reordenação
        ttk.Button(reorder_frame, text="⬆⬆ Topo", width=8,
                  command=self.move_to_top).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(reorder_frame, text="⬆ Subir", width=8,
                  command=self.move_up).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(reorder_frame, text="⬇ Descer", width=8,
                  command=self.move_down).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(reorder_frame, text="⬇⬇ Final", width=8,
                  command=self.move_to_bottom).pack(side=tk.LEFT, padx=(0, 2))
        
        # Frame da lista de músicas
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview para mostrar as músicas
        columns = ('Ordem', 'Nome', 'BPM', 'Nota', 'Volume', 'Duração')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=20)
        
        # Configurar colunas
        self.tree.heading('#0', text='')
        self.tree.column('#0', width=0, stretch=False)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Ordem':
                self.tree.column(col, width=60, anchor=tk.CENTER)
            elif col == 'Nome':
                self.tree.column(col, width=350, anchor=tk.W)
            elif col == 'BPM':
                self.tree.column(col, width=80, anchor=tk.CENTER)
            elif col == 'Nota':
                self.tree.column(col, width=80, anchor=tk.CENTER)
            elif col == 'Volume':
                self.tree.column(col, width=80, anchor=tk.CENTER)
            elif col == 'Duração':
                self.tree.column(col, width=100, anchor=tk.CENTER)
        
        # Scrollbar para a treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind para duplo clique (play música)
        self.tree.bind('<Double-1>', self.play_music)
        
        # Bind para seleção simples (não interferir com play)
        self.tree.bind('<Button-1>', self.on_single_click)
        
        # Bind melhorado para drag and drop (só funciona com arrastar)
        self.tree.bind('<B1-Motion>', self.on_drag)
        self.tree.bind('<ButtonRelease-1>', self.on_drop)
        
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
        self.drag_data = {'item': None, 'index': None, 'dragging': False}
    
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
                'volume': "N/A",
                'duration': "N/A"
            }
    
    def update_progress(self, value):
        self.progress_bar['value'] = value
        self.root.update_idletasks()
    
    def update_music_list(self):
        # Limpar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Adicionar músicas
        for i, music in enumerate(self.music_files, 1):
            self.tree.insert('', 'end', values=(
                i, music['name'], music['bpm'], music['key'], music['volume'], music['duration']
            ))
        
        self.progress_bar.pack_forget()
        self.progress_label.config(text=f"{len(self.music_files)} músicas carregadas")
        self.organize_btn.config(state=tk.NORMAL)
    
    def play_music(self, event):
        if not self.pygame_initialized:
            messagebox.showerror("Erro", "Sistema de áudio não inicializado")
            return
            
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            if values:
                index = int(values[0]) - 1
                if 0 <= index < len(self.music_files):
                    file_path = self.music_files[index]['path']
                    try:
                        pygame.mixer.music.load(file_path)
                        pygame.mixer.music.play()
                        self.current_playing = file_path
                        
                        # Obter duração da música
                        duration_str = self.music_files[index]['duration']
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
                        self.current_music_label.config(
                            text=f"Tocando: {self.music_files[index]['name']}"
                        )
                        self.time_current_label.config(text="00:00")
                        
                        # Manter o item selecionado
                        self.tree.focus(item)
                        
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
    
    def on_single_click(self, event):
        # Apenas armazena a posição inicial, mas não inicia drag imediatamente
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item:
            self.drag_data = {
                'item': item, 
                'index': self.tree.index(item),
                'start_x': event.x,
                'start_y': event.y,
                'dragging': False
            }
    
    def on_drag(self, event):
        # Só considera drag se mouse se moveu uma distância significativa
        if self.drag_data.get('item') and not self.drag_data.get('dragging'):
            start_x = self.drag_data.get('start_x', 0)
            start_y = self.drag_data.get('start_y', 0)
            
            # Verificar se moveu pelo menos 10 pixels
            if abs(event.x - start_x) > 10 or abs(event.y - start_y) > 10:
                self.drag_data['dragging'] = True
                print("Iniciando arrastar...")  # Debug
    
    def on_drop(self, event):
        # Só executar drop se realmente estava arrastando
        if self.drag_data.get('item') and self.drag_data.get('dragging'):
            # Encontrar item de destino
            target = self.tree.identify_row(event.y)
            if target and target != self.drag_data['item']:
                # Obter dados do item arrastado
                values = self.tree.item(self.drag_data['item'], 'values')
                
                # Remover item da posição original
                self.tree.delete(self.drag_data['item'])
                
                # Inserir na nova posição
                target_index = self.tree.index(target)
                new_item = self.tree.insert('', target_index, values=values)
                
                # Reorganizar lista interna
                old_index = self.drag_data['index']
                music_item = self.music_files.pop(old_index)
                self.music_files.insert(target_index, music_item)
                
                # Atualizar números de ordem
                self.update_order_numbers()
                
                # Reselecionar item movido
                self.tree.selection_set(new_item)
                self.tree.focus(new_item)
                
                print("Drop executado!")  # Debug
        
        # Limpar dados de drag
        self.drag_data = {'item': None, 'index': None, 'dragging': False}
    
    def update_order_numbers(self):
        for i, item in enumerate(self.tree.get_children()):
            values = list(self.tree.item(item, 'values'))
            values[0] = str(i + 1)  # Atualizar número da ordem
            self.tree.item(item, values=values)
    
    def organize_set(self):
        if not self.music_files:
            messagebox.showwarning("Aviso", "Nenhuma música carregada")
            return
        
        # Selecionar pasta de destino
        dest_folder = filedialog.askdirectory(title="Selecionar pasta para salvar o set organizado")
        if not dest_folder:
            return
        
        try:
            # Criar pasta se não existir
            os.makedirs(dest_folder, exist_ok=True)
            
            # Copiar arquivos na ordem atual
            for i, music in enumerate(self.music_files, 1):
                source_path = music['path']
                extension = Path(source_path).suffix
                new_name = f"{i:02d} - {music['name']}"
                dest_path = os.path.join(dest_folder, new_name)
                
                shutil.copy2(source_path, dest_path)
            
            messagebox.showinfo("Sucesso", 
                              f"Set organizado com sucesso!\n{len(self.music_files)} músicas copiadas para:\n{dest_folder}")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao organizar set: {e}")

    def get_selected_index(self):
        """Retorna o índice da música selecionada ou None se nenhuma estiver selecionada"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            if values:
                return int(values[0]) - 1  # Converter para índice 0-based
        return None
    
    def move_to_top(self):
        """Move a música selecionada para o topo da lista"""
        index = self.get_selected_index()
        if index is None or index == 0:
            return  # Nada selecionado ou já está no topo
        
        # Mover na lista interna
        music_item = self.music_files.pop(index)
        self.music_files.insert(0, music_item)
        
        # Atualizar interface
        self.update_music_list()
        
        # Reselecionar o item na nova posição
        first_item = self.tree.get_children()[0]
        self.tree.selection_set(first_item)
        self.tree.focus(first_item)
    
    def move_up(self):
        """Move a música selecionada uma posição para cima"""
        index = self.get_selected_index()
        if index is None or index == 0:
            return  # Nada selecionado ou já está no topo
        
        # Trocar posições na lista interna
        self.music_files[index], self.music_files[index-1] = self.music_files[index-1], self.music_files[index]
        
        # Atualizar interface
        self.update_music_list()
        
        # Reselecionar o item na nova posição
        new_item = self.tree.get_children()[index-1]
        self.tree.selection_set(new_item)
        self.tree.focus(new_item)
    
    def move_down(self):
        """Move a música selecionada uma posição para baixo"""
        index = self.get_selected_index()
        if index is None or index >= len(self.music_files) - 1:
            return  # Nada selecionado ou já está no final
        
        # Trocar posições na lista interna
        self.music_files[index], self.music_files[index+1] = self.music_files[index+1], self.music_files[index]
        
        # Atualizar interface
        self.update_music_list()
        
        # Reselecionar o item na nova posição
        new_item = self.tree.get_children()[index+1]
        self.tree.selection_set(new_item)
        self.tree.focus(new_item)
    
    def move_to_bottom(self):
        """Move a música selecionada para o final da lista"""
        index = self.get_selected_index()
        if index is None or index >= len(self.music_files) - 1:
            return  # Nada selecionado ou já está no final
        
        # Mover na lista interna
        music_item = self.music_files.pop(index)
        self.music_files.append(music_item)
        
        # Atualizar interface
        self.update_music_list()
        
        # Reselecionar o item na nova posição
        last_item = self.tree.get_children()[-1]
        self.tree.selection_set(last_item)
        self.tree.focus(last_item)

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

def main():
    root = tk.Tk()
    app = DJSetOrganizer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
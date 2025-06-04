#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '4.0')
try:
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, GLib, Gio, GObject, Adw, Gdk
    HAS_ADW = True
except (ValueError, ImportError):
    from gi.repository import Gtk, GLib, Gio, GObject, Gdk
    HAS_ADW = False

import os
import threading
import time
import subprocess
from pathlib import Path
import traceback
import datetime

from deschavezip.zip_cracker import ZipCracker

@Gtk.Template(filename=str(Path(__file__).parent / "app_window.ui"))
class AppWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "AppWindow"

    # Template widgets
    stack = Gtk.Template.Child()
    zip_file_button = Gtk.Template.Child()
    wordlist_button = Gtk.Template.Child()
    start_button = Gtk.Template.Child()
    pause_button = Gtk.Template.Child()
    cancel_button = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()
    log_buffer = Gtk.Template.Child()
    log_view = Gtk.Template.Child()
    
    # Novos widgets de informação de arquivo ZIP
    zip_name_label = Gtk.Template.Child()
    zip_encryption_label = Gtk.Template.Child()
    zip_size_label = Gtk.Template.Child()
    zip_files_label = Gtk.Template.Child()
    
    # Novos widgets de informação de wordlist
    wordlist_name_label = Gtk.Template.Child()
    wordlist_lines_label = Gtk.Template.Child()
    wordlist_size_label = Gtk.Template.Child()
    wordlist_time_label = Gtk.Template.Child()
    
    # Cards
    zip_card = Gtk.Template.Child()
    wordlist_card = Gtk.Template.Child()
    
    # Widgets do painel de estatísticas
    stats_panel = Gtk.Template.Child()
    speed_label = Gtk.Template.Child()
    eta_label = Gtk.Template.Child()
    progress_label = Gtk.Template.Child()
    attempts_label = Gtk.Template.Child()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.set_title("DeschaveZIP")
        self.set_default_size(800, 600)
        
        # Estado da aplicação
        self.zip_path = None
        self.wordlist_path = None
        self.cracker = None
        self.is_running = False
        self.is_paused = False
        self.total_passwords = 0
        self.current_password = 0
        self.zip_info = None
        
        # Estatísticas
        self.start_time = None
        self.passwords_per_second = 0
        self.last_update_time = None
        self.last_password_count = 0
        self.total_attempts = 0
        
        # Definir estilo visual para os cartões
        self.aplicar_estilo_cartoes()
        
        # Ocultar painel de estatísticas inicialmente
        self.stats_panel.set_visible(False)
        
        # Conectar sinais
        self.zip_file_button.connect("clicked", self.on_zip_file_clicked)
        self.wordlist_button.connect("clicked", self.on_wordlist_clicked)
        self.start_button.connect("clicked", self.on_start_clicked)
        self.pause_button.connect("clicked", self.on_pause_clicked)
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        
        # Desativar botões até que os arquivos sejam selecionados
        self.update_ui_state()
    
    def aplicar_estilo_cartoes(self):
        """Aplica estilo visual aos cartões de arquivos"""
        css_provider = Gtk.CssProvider()
        css = """
        .card {
            border: 1px solid alpha(#000, 0.1);
            border-radius: 12px;
            background-color: alpha(#fff, 0.05);
            box-shadow: 0 2px 4px alpha(#000, 0.1);
            transition: all 200ms ease;
        }
        
        .card:hover {
            box-shadow: 0 4px 8px alpha(#000, 0.2);
            background-color: alpha(#fff, 0.08);
        }
        
        .card-selected {
            border: 2px solid @accent_bg_color;
            background-color: alpha(@accent_bg_color, 0.1);
        }
        
        .stat-card {
            border-radius: 6px;
            background-color: alpha(#fff, 0.03);
            transition: all 200ms ease;
        }
        
        .stats-panel {
            border-top: 1px solid alpha(#fff, 0.1);
            border-bottom: 1px solid alpha(#fff, 0.1);
            padding: 8px 0;
        }
        """
        css_provider.load_from_data(css.encode())
        
        # Em GTK4, precisamos obter o display de forma um pouco diferente
        display = self.get_display()
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def on_zip_file_clicked(self, button):
        self.select_file("zip")
    
    def on_wordlist_clicked(self, button):
        self.select_file("wordlist")
    
    def select_file(self, type_):
        """Usa o seletor de arquivos nativo do sistema"""
        try:
            # Em GTK4, vamos usar o zenity que está disponível na maioria dos sistemas Linux com GNOME
            file_type = "Arquivos ZIP" if type_ == "zip" else "Arquivos de texto"
            file_pattern = "*.zip" if type_ == "zip" else "*.txt"
            
            # Preparar o comando zenity
            cmd = [
                "zenity", "--file-selection", 
                "--title", f"Selecionar {'arquivo ZIP' if type_ == 'zip' else 'wordlist'}",
                "--file-filter", f"{file_type} | {file_pattern}"
            ]
            
            # Executar zenity e capturar a saída
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip()
                if os.path.exists(path):
                    if type_ == "zip":
                        self.zip_path = path
                        self.zip_file_button.set_label("Selecionar outro arquivo")
                        self.update_zip_info(path)
                        self.log(f"Arquivo ZIP selecionado: {path}")
                        # Aplicar classe de estilo ao card
                        self.zip_card.add_css_class("card-selected")
                    else:
                        self.wordlist_path = path
                        self.wordlist_button.set_label("Selecionar outra wordlist")
                        self.update_wordlist_info(path)
                        self.log(f"Wordlist selecionada: {path}")
                        # Aplicar classe de estilo ao card
                        self.wordlist_card.add_css_class("card-selected")
                    self.update_ui_state()
                else:
                    self.log(f"Erro: Arquivo não encontrado - {path}")
        except Exception as e:
            self.log(f"Erro ao abrir seletor de arquivos: {str(e)}")
            # Fallback para o modo texto
            self.ask_file_path(type_)
    
    def update_zip_info(self, zip_path):
        """Atualiza as informações do arquivo ZIP nos widgets do cartão"""
        if not zip_path or not os.path.exists(zip_path):
            return
        
        # Atualizar nome do arquivo
        filename = os.path.basename(zip_path)
        self.zip_name_label.set_text(filename)
        
        # Atualizar tamanho do arquivo
        size_bytes = os.path.getsize(zip_path)
        if size_bytes < 1024:
            size_str = f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes/1024:.1f} KB"
        else:
            size_str = f"{size_bytes/(1024*1024):.1f} MB"
        self.zip_size_label.set_text(f"Tamanho: {size_str}")
        
        try:
            # Obter informações adicionais usando o ZipCracker
            temp_cracker = ZipCracker(zip_path, "")
            encryption_info = temp_cracker.detect_encryption_type()
            self.zip_info = encryption_info
            
            # Atualizar tipo de criptografia
            if encryption_info["is_encrypted"]:
                self.zip_encryption_label.set_text(f"Criptografia: {encryption_info['encryption_type']}")
            else:
                self.zip_encryption_label.set_text("Criptografia: Nenhuma")
            
            # Atualizar contagem de arquivos
            if encryption_info["encrypted_files"] > 0:
                file_text = (f"Arquivos: {encryption_info['encrypted_files']} protegidos "
                            f"de {encryption_info['total_files']} total")
            else:
                file_text = f"Arquivos: {encryption_info['total_files']} (não protegidos)"
            self.zip_files_label.set_text(file_text)
        except Exception as e:
            self.log(f"Erro ao analisar arquivo ZIP: {str(e)}")
            self.zip_encryption_label.set_text("Criptografia: Desconhecida")
            self.zip_files_label.set_text("Arquivos: Erro ao analisar")
    
    def update_wordlist_info(self, wordlist_path):
        """Atualiza as informações da wordlist nos widgets do cartão"""
        if not wordlist_path or not os.path.exists(wordlist_path):
            return
        
        # Atualizar nome do arquivo
        filename = os.path.basename(wordlist_path)
        self.wordlist_name_label.set_text(filename)
        
        # Atualizar tamanho do arquivo
        size_bytes = os.path.getsize(wordlist_path)
        if size_bytes < 1024:
            size_str = f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes/1024:.1f} KB"
        else:
            size_str = f"{size_bytes/(1024*1024):.1f} MB"
        self.wordlist_size_label.set_text(f"Tamanho: {size_str}")
        
        try:
            # Contar número de senhas
            with open(wordlist_path, 'r', errors='ignore') as f:
                num_passwords = sum(1 for line in f if line.strip())
            
            self.total_passwords = num_passwords
            self.wordlist_lines_label.set_text(f"Senhas: {num_passwords:,}".replace(",", "."))
            
            # Calcular tempo estimado (assume 500 senhas/segundo em média)
            if num_passwords > 0:
                segundos_estimados = num_passwords / 500
                if segundos_estimados < 60:
                    tempo_str = f"{segundos_estimados:.1f} segundos"
                elif segundos_estimados < 3600:
                    tempo_str = f"{segundos_estimados/60:.1f} minutos"
                else:
                    tempo_str = f"{segundos_estimados/3600:.1f} horas"
                self.wordlist_time_label.set_text(f"Tempo estimado: {tempo_str}")
            else:
                self.wordlist_time_label.set_text("Tempo estimado: -")
        except Exception as e:
            self.log(f"Erro ao analisar wordlist: {str(e)}")
            self.wordlist_lines_label.set_text("Senhas: Erro ao contar")
            self.wordlist_time_label.set_text("Tempo estimado: -")
    
    def ask_file_path(self, type_):
        """Abre uma caixa de diálogo simples para entrada de texto (fallback)"""
        dialog = Gtk.Window(title=f"Selecionar {'arquivo ZIP' if type_ == 'zip' else 'wordlist'}")
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.set_default_size(400, 150)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        dialog.set_child(box)
        
        label = Gtk.Label()
        label.set_text(f"Digite o caminho completo para o {'arquivo ZIP' if type_ == 'zip' else 'wordlist'}:")
        box.append(label)
        
        entry = Gtk.Entry()
        box.append(entry)
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        box.append(button_box)
        
        cancel_button = Gtk.Button(label="Cancelar")
        button_box.append(cancel_button)
        
        ok_button = Gtk.Button(label="OK")
        ok_button.add_css_class("suggested-action")
        button_box.append(ok_button)
        
        def on_cancel(button):
            dialog.destroy()
        
        def on_ok(button):
            path = entry.get_text()
            if os.path.exists(path):
                if type_ == 'zip':
                    self.zip_path = path
                    self.zip_file_button.set_label("Selecionar outro arquivo")
                    self.update_zip_info(path)
                    self.log(f"Arquivo ZIP selecionado: {path}")
                    # Aplicar classe de estilo ao card
                    self.zip_card.add_css_class("card-selected")
                else:
                    self.wordlist_path = path
                    self.wordlist_button.set_label("Selecionar outra wordlist")
                    self.update_wordlist_info(path)
                    self.log(f"Wordlist selecionada: {path}")
                    # Aplicar classe de estilo ao card
                    self.wordlist_card.add_css_class("card-selected")
                self.update_ui_state()
                dialog.destroy()
            else:
                error_label = Gtk.Label()
                error_label.set_text(f"Erro: Arquivo não encontrado")
                error_label.add_css_class("error-message")
                box.append(error_label)
        
        cancel_button.connect("clicked", on_cancel)
        ok_button.connect("clicked", on_ok)
        
        dialog.present()
    
    def on_start_clicked(self, button):
        if self.is_paused:
            self.is_paused = False
            self.log("Retomando processo...")
        else:
            self.start_cracking()
        
        self.update_ui_state()
    
    def on_pause_clicked(self, button):
        self.is_paused = True
        self.log("Processo pausado.")
        self.update_ui_state()
    
    def on_cancel_clicked(self, button):
        if self.is_running:
            self.is_running = False
            self.is_paused = False
            self.log("Processo cancelado.")
            
        self.progress_bar.set_fraction(0)
        
        # Não ocultar o painel de estatísticas
        # self.stats_panel.set_visible(False)
        
        self.update_ui_state()
    
    def start_cracking(self):
        self.is_running = True
        self.is_paused = False
        
        self.log("Iniciando processo de quebra de senha...")
        self.log(f"Arquivo: {self.zip_path}")
        self.log(f"Wordlist: {self.wordlist_path}")
        
        # Inicializar variáveis de estatísticas
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.last_password_count = 0
        self.total_attempts = 0
        self.passwords_per_second = 0
        
        # Mostrar o painel de estatísticas
        self.stats_panel.set_visible(True)
        
        # Resetar as estatísticas
        self.speed_label.set_text("0 senhas/s")
        self.eta_label.set_text("--:--:--")
        self.progress_label.set_text("0/0 (0%)")
        self.attempts_label.set_text("0")
        
        # Verificar o arquivo ZIP
        self.check_zip_file()
        
        # Contar o número total de senhas na wordlist
        try:
            with open(self.wordlist_path, 'r', errors='ignore') as f:
                self.total_passwords = sum(1 for line in f if line.strip())
            
            self.log(f"Total de senhas a testar: {self.total_passwords}")
        except Exception as e:
            self.log(f"Erro ao ler wordlist: {str(e)}")
            self.is_running = False
            self.update_ui_state()
            return
        
        # Iniciar o cracker em uma thread separada
        self.cracker = ZipCracker(self.zip_path, self.wordlist_path)
        thread = threading.Thread(target=self.cracking_thread)
        thread.daemon = True
        thread.start()
    
    def check_zip_file(self):
        """
        Verifica o arquivo ZIP selecionado e atualiza o log com informações sobre
        o arquivo, incluindo tipo de criptografia, tamanho e número de arquivos.
        """
        selected_file = self.zip_path
        if not selected_file:
            self.log("Selecione um arquivo ZIP primeiro")
            return
            
        if not os.path.exists(selected_file):
            self.log(f"Arquivo não encontrado: {selected_file}")
            return
            
        file_size_mb = os.path.getsize(selected_file) / (1024 * 1024)
        
        try:
            import zipfile
            from deschavezip.zip_cracker import ZipCracker
            
            # Usar o detector avançado de criptografia
            temp_cracker = ZipCracker(selected_file, "")
            encryption_info = temp_cracker.detect_encryption_type()
            
            self.log(f"Informações do arquivo ZIP:")
            self.log(f"- Nome: {os.path.basename(selected_file)}")
            self.log(f"- Tamanho: {os.path.getsize(selected_file) / 1024:.2f} KB")
            self.log(f"- Total de arquivos: {encryption_info['total_files']}")
            
            if encryption_info["is_encrypted"]:
                self.log(f"- Arquivos protegidos: {encryption_info['encrypted_files']} de {encryption_info['total_files']}")
                
                is_aes = encryption_info["encryption_type"].startswith("AES")
                if is_aes:
                    self.log(f"- 🔒 Tipo de criptografia: {encryption_info['encryption_type']}")
                    
                    if encryption_info.get("has_external_support"):
                        self.log(f"  ✅ 7-Zip encontrado! Será utilizado para quebra de senha AES.")
                    else:
                        self.log(f"  ⚠️ ALERTA: Este arquivo usa AES e requer 7-Zip para quebra de senha!")
                        self.log(f"  📋 Instalação:")
                        self.log(f"    • Ubuntu/Debian: sudo apt-get install p7zip-full")
                        self.log(f"    • Fedora: sudo dnf install p7zip p7zip-plugins")
                        self.log(f"    • Arch Linux: sudo pacman -S p7zip")
                else:
                    self.log(f"- 🔑 Tipo de criptografia: {encryption_info['encryption_type']}")
            else:
                self.log("- Arquivo não protegido por senha.")
            
            # Exibir informações detalhadas dos arquivos criptografados
            if encryption_info["encrypted_files"] > 0:
                self.log(f"\nArquivos criptografados:")
                for file_info in encryption_info["files_info"]:
                    if file_info["encrypted"]:
                        self.log(f"  • {file_info['name']} ({file_info['size']/1024:.1f} KB)")
                        self.log(f"    → Criptografia: {file_info['encryption_type']}")
                        self.log(f"    → Compressão: {file_info['compression']}")
                
        except Exception as e:
            self.log(f"Erro ao verificar arquivo ZIP: {str(e)}")
    
    def cracking_thread(self):
        for progress in self.cracker.crack_password(
            pause_check=lambda: self.is_paused,
            cancel_check=lambda: not self.is_running
        ):
            self.current_password = progress["current_password"]
            self.total_attempts += 1
            GLib.idle_add(self.update_progress, progress)
            
            # Atualizar estatísticas a cada 1 segundo para não sobrecarregar a UI
            current_time = time.time()
            if current_time - self.last_update_time >= 0.5:  # Atualiza a cada 0.5 segundos
                self.update_statistics()
                self.last_update_time = current_time
    
    def update_statistics(self):
        """Atualiza as estatísticas de desempenho"""
        if not self.is_running or self.is_paused:
            return
        
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time
        passwords_processed = self.current_password - self.last_password_count
        
        # Calcular senhas por segundo
        if elapsed_time > 0:
            self.passwords_per_second = passwords_processed / elapsed_time
        
        # Atualizar a UI com as estatísticas
        GLib.idle_add(self.update_stats_ui)
        
        # Armazenar os valores atuais para o próximo cálculo
        self.last_password_count = self.current_password
    
    def update_stats_ui(self):
        """Atualiza os widgets de UI com as estatísticas mais recentes"""
        if not self.is_running:
            return False
        
        # Atualizar velocidade
        speed_text = f"{self.passwords_per_second:.1f} senhas/s"
        self.speed_label.set_text(speed_text)
        
        # Atualizar tempo restante estimado (ETA)
        if self.passwords_per_second > 0:
            remaining_passwords = self.total_passwords - self.current_password
            seconds_remaining = remaining_passwords / self.passwords_per_second
            
            eta = self.format_time_remaining(seconds_remaining)
            self.eta_label.set_text(eta)
        else:
            self.eta_label.set_text("--:--:--")
        
        # Atualizar progresso
        if self.total_passwords > 0:
            progress_percent = (self.current_password / self.total_passwords) * 100
            progress_text = f"{self.current_password:,}/{self.total_passwords:,} ({progress_percent:.1f}%)".replace(",", ".")
            self.progress_label.set_text(progress_text)
        else:
            self.progress_label.set_text("0/0 (0%)")
        
        # Atualizar tentativas
        self.attempts_label.set_text(f"{self.total_attempts:,}".replace(",", "."))
        
        return False  # Sinaliza que a função terminou e não deve ser chamada novamente
    
    def format_time_remaining(self, seconds):
        """Formata o tempo restante em horas:minutos:segundos"""
        if seconds < 0:
            return "--:--:--"
            
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    
    def update_progress(self, progress):
        if not self.is_running:
            return
        
        password = progress.get("password", None)
        current = progress.get("current_password", 0)
        current_text = progress.get("current_text", "")
        error = progress.get("error", None)
        info = progress.get("info", None)
        warning = progress.get("warning", None)
        encryption_info = progress.get("encryption_info", None)
        method = progress.get("method", None)
        
        # Atualizar barra de progresso
        fraction = current / self.total_passwords if self.total_passwords > 0 else 0
        self.progress_bar.set_fraction(fraction)
        
        # Atualizar log
        if password:
            method_text = ""
            method_icon = ""
            if method == "7z":
                method_text = "usando 7-Zip"
                method_icon = "🛠️"
            elif method == "zipfile":
                method_text = "usando método interno"
                method_icon = "🔧"
                
            self.log("\n" + "=" * 50)
            self.log("🎉 SENHA ENCONTRADA! 🎉")
            self.log("=" * 50)
            self.log(f"🔑 Senha: {password}")
            self.log(f"🔐 Método: {method_icon} {method_text}")
            self.log("=" * 50 + "\n")
            
            self.is_running = False
            
            # Não ocultar o painel de estatísticas
            # self.stats_panel.set_visible(False)
            
            self.update_ui_state()
        elif error:
            if "Nenhuma senha encontrada" in error:
                self.log("\n" + "=" * 50)
                self.log("❌ SENHA NÃO ENCONTRADA ❌")
                self.log("=" * 50)
                self.log(f"📋 {error}")
                self.log(f"💡 Tente usar uma wordlist diferente ou maior")
                self.log("=" * 50 + "\n")
            else:
                self.log(f"❌ ERRO: {error}")
            self.is_running = False
            
            # Não ocultar o painel de estatísticas
            # self.stats_panel.set_visible(False)
            
            self.update_ui_state()
        elif warning:
            self.log(f"⚠️ {warning}")
            if encryption_info and encryption_info.get("is_encrypted"):
                self.log(f"  - Tipo de criptografia: {encryption_info.get('encryption_type', 'Desconhecido')}")
                self.log(f"  - Arquivos protegidos: {encryption_info.get('encrypted_files', 0)} de {encryption_info.get('total_files', 0)}")
                
                if not encryption_info.get("has_external_support", False):
                    self.log(f"  - Para suporte a AES, instale o 7-Zip:")
                    self.log(f"    sudo apt-get install p7zip-full")
                
                self.log(f"  - A quebra continuará, mas poderá falhar para este tipo de criptografia.")
        elif info:
            self.log(f"ℹ️ {info}")
        elif current_text:
            if current % 50 == 0 or current <= 5 or current > self.total_passwords - 5:  # Mostrar mais no início e fim
                self.log(f"🔍 Testando: {current_text} ({current}/{self.total_passwords})")
        
        return False
    
    def log(self, message):
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, f"{message}\n")
        
        # Auto-scroll para o final
        end_iter = self.log_buffer.get_end_iter()
        mark = self.log_buffer.create_mark(None, end_iter, False)
        self.log_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
    
    def update_ui_state(self):
        files_selected = self.zip_path is not None and self.wordlist_path is not None
        
        self.start_button.set_sensitive(
            (files_selected and not self.is_running) or self.is_paused)
        self.pause_button.set_sensitive(self.is_running and not self.is_paused)
        self.cancel_button.set_sensitive(self.is_running)
        
        self.zip_file_button.set_sensitive(not self.is_running)
        self.wordlist_button.set_sensitive(not self.is_running)
        
        # Atualiza a aparência dos cards conforme o estado dos arquivos
        self.reset_ui_cards()

    def enable_cracking(self):
        self.start_button.set_sensitive(False)
        self.pause_button.set_sensitive(True)
        self.cancel_button.set_sensitive(True)
        self.zip_file_button.set_sensitive(False)
        self.wordlist_button.set_sensitive(False)

    def disable_cracking(self):
        self.start_button.set_sensitive(True)
        self.pause_button.set_sensitive(False)
        self.cancel_button.set_sensitive(False)
        self.zip_file_button.set_sensitive(True)
        self.wordlist_button.set_sensitive(True)

    def reset_ui_cards(self):
        """Reseta a aparência dos cards quando nenhum arquivo está selecionado"""
        if not self.zip_path:
            self.zip_name_label.set_text("Nenhum arquivo selecionado")
            self.zip_encryption_label.set_text("Tipo de criptografia: -")
            self.zip_size_label.set_text("Tamanho: -")
            self.zip_files_label.set_text("Arquivos: -")
            self.zip_card.remove_css_class("card-selected")
        
        if not self.wordlist_path:
            self.wordlist_name_label.set_text("Nenhum arquivo selecionado")
            self.wordlist_lines_label.set_text("Senhas: -")
            self.wordlist_size_label.set_text("Tamanho: -")
            self.wordlist_time_label.set_text("Tempo estimado: -")
            self.wordlist_card.remove_css_class("card-selected") 
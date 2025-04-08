#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '4.0')
try:
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, GLib, Gio, GObject, Adw
    HAS_ADW = True
except (ValueError, ImportError):
    from gi.repository import Gtk, GLib, Gio, GObject
    HAS_ADW = False

import os
import threading
import time
import subprocess
from pathlib import Path

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
        
        # Conectar sinais
        self.zip_file_button.connect("clicked", self.on_zip_file_clicked)
        self.wordlist_button.connect("clicked", self.on_wordlist_clicked)
        self.start_button.connect("clicked", self.on_start_clicked)
        self.pause_button.connect("clicked", self.on_pause_clicked)
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        
        # Desativar botões até que os arquivos sejam selecionados
        self.update_ui_state()
    
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
                        self.zip_file_button.set_label(os.path.basename(path))
                        self.log(f"Arquivo ZIP selecionado: {path}")
                    else:
                        self.wordlist_path = path
                        self.wordlist_button.set_label(os.path.basename(path))
                        self.log(f"Wordlist selecionada: {path}")
                    self.update_ui_state()
                else:
                    self.log(f"Erro: Arquivo não encontrado - {path}")
        except Exception as e:
            self.log(f"Erro ao abrir seletor de arquivos: {str(e)}")
            # Fallback para o modo texto
            self.ask_file_path(type_)
    
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
                    self.zip_file_button.set_label(os.path.basename(path))
                    self.log(f"Arquivo ZIP selecionado: {path}")
                else:
                    self.wordlist_path = path
                    self.wordlist_button.set_label(os.path.basename(path))
                    self.log(f"Wordlist selecionada: {path}")
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
        self.update_ui_state()
    
    def start_cracking(self):
        self.is_running = True
        self.is_paused = False
        
        self.log("Iniciando processo de quebra de senha...")
        self.log(f"Arquivo: {self.zip_path}")
        self.log(f"Wordlist: {self.wordlist_path}")
        
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
        """Verifica e exibe informações sobre o arquivo ZIP"""
        try:
            import zipfile
            from deschavezip.zip_cracker import ZipCracker
            
            # Usar o detector avançado de criptografia
            temp_cracker = ZipCracker(self.zip_path, "")
            encryption_info = temp_cracker.detect_encryption_type()
            
            self.log(f"Informações do arquivo ZIP:")
            self.log(f"- Nome: {os.path.basename(self.zip_path)}")
            self.log(f"- Tamanho: {os.path.getsize(self.zip_path) / 1024:.2f} KB")
            self.log(f"- Total de arquivos: {encryption_info['total_files']}")
            
            if encryption_info["is_encrypted"]:
                self.log(f"- Arquivos protegidos: {encryption_info['encrypted_files']} de {encryption_info['total_files']}")
                
                is_aes = encryption_info["encryption_type"].startswith("AES")
                if is_aes:
                    self.log(f"- 🔒 Tipo de criptografia: \033[1;33m{encryption_info['encryption_type']}\033[0m")
                    
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
            GLib.idle_add(self.update_progress, progress)
    
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
                
            self.log(f"🔓 SENHA ENCONTRADA: \033[1;32m{password}\033[0m {method_icon} ({method_text})")
            self.is_running = False
            self.update_ui_state()
        elif error:
            self.log(f"❌ ERRO: {error}")
            self.is_running = False
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
            if self.current_password % 100 == 0:  # Mostrar apenas a cada 100 senhas para reduzir log
                self.log(f"Testando senha #{current}: {current_text} ({current}/{self.total_passwords})")
        
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
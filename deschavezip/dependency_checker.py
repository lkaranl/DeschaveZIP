#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess
import platform

def check_dependencies():
    """
    Verifica se todas as dependências do sistema estão instaladas.
    Retorna True se todas as dependências obrigatórias estiverem instaladas,
    False caso contrário.
    """
    # Lista de dependências obrigatórias e opcionais
    dependencies = {
        "gtk4": {
            "name": "GTK 4.0",
            "mandatory": True,
            "apt": "gir1.2-gtk-4.0",
            "dnf": "gtk4",
            "pacman": "gtk4"
        },
        "zenity": {
            "name": "Zenity",
            "mandatory": True,
            "apt": "zenity",
            "dnf": "zenity",
            "pacman": "zenity"
        },
        "libadwaita": {
            "name": "Libadwaita",
            "mandatory": False,
            "apt": "gir1.2-adw-1",
            "dnf": "libadwaita",
            "pacman": "libadwaita"
        },
        "p7zip": {
            "name": "7-Zip",
            "mandatory": False,  # Só é necessário para arquivos com criptografia AES
            "apt": "p7zip-full",
            "dnf": "p7zip p7zip-plugins",
            "pacman": "p7zip"
        }
    }
    
    # Verifica quais dependências estão faltando
    missing_deps = []
    missing_mandatory = False
    
    print("Verificando dependências do sistema...")
    
    # Verifica GTK 4.0
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk
        print("✅ GTK 4.0: Instalado")
    except (ImportError, ValueError):
        print("❌ GTK 4.0: Não encontrado (obrigatório)")
        missing_deps.append("gtk4")
        missing_mandatory = True
    
    # Verifica Libadwaita
    try:
        import gi
        gi.require_version('Adw', '1')
        from gi.repository import Adw
        print("✅ Libadwaita: Instalado")
    except (ImportError, ValueError):
        print("ℹ️ Libadwaita: Não encontrado (opcional)")
        missing_deps.append("libadwaita")
    
    # Verifica Zenity
    zenity_path = shutil.which("zenity")
    if zenity_path:
        print("✅ Zenity: Instalado")
    else:
        print("❌ Zenity: Não encontrado (obrigatório)")
        missing_deps.append("zenity")
        missing_mandatory = True
    
    # Verifica 7-Zip
    p7zip_path = shutil.which("7z") or shutil.which("7za")
    if p7zip_path:
        print("✅ 7-Zip: Instalado")
    else:
        print("ℹ️ 7-Zip: Não encontrado (recomendado para arquivos AES)")
        missing_deps.append("p7zip")
    
    # Se houver dependências faltando, mostra como instalá-las
    if missing_deps:
        print("\nDependências faltando:")
        
        # Detecta o sistema operacional
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                os_info = {}
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        os_info[key] = value.strip('"')
            
            # Debian/Ubuntu
            if os_info.get("ID") in ["debian", "ubuntu", "linuxmint", "pop"]:
                print("\nPara instalar no Debian/Ubuntu/Mint/Pop_OS:")
                cmd = "sudo apt install"
                for dep in missing_deps:
                    cmd += f" {dependencies[dep]['apt']}"
                print(f"  {cmd}")
            
            # Fedora/RHEL
            elif os_info.get("ID") in ["fedora", "rhel", "centos"]:
                print("\nPara instalar no Fedora/RHEL/CentOS:")
                cmd = "sudo dnf install"
                for dep in missing_deps:
                    cmd += f" {dependencies[dep]['dnf']}"
                print(f"  {cmd}")
            
            # Arch Linux
            elif os_info.get("ID") in ["arch", "manjaro", "endeavouros"]:
                print("\nPara instalar no Arch Linux/Manjaro/EndeavourOS:")
                cmd = "sudo pacman -S"
                for dep in missing_deps:
                    cmd += f" {dependencies[dep]['pacman']}"
                print(f"  {cmd}")
            
            # Outros
            else:
                print_all_install_instructions(missing_deps, dependencies)
        else:
            print_all_install_instructions(missing_deps, dependencies)
    
    return not missing_mandatory

def print_all_install_instructions(missing_deps, dependencies):
    """Exibe instruções de instalação para todos os sistemas suportados"""
    print("\nPara instalar no Debian/Ubuntu/Mint:")
    cmd = "sudo apt install"
    for dep in missing_deps:
        cmd += f" {dependencies[dep]['apt']}"
    print(f"  {cmd}")
    
    print("\nPara instalar no Fedora/RHEL/CentOS:")
    cmd = "sudo dnf install"
    for dep in missing_deps:
        cmd += f" {dependencies[dep]['dnf']}"
    print(f"  {cmd}")
    
    print("\nPara instalar no Arch Linux/Manjaro:")
    cmd = "sudo pacman -S"
    for dep in missing_deps:
        cmd += f" {dependencies[dep]['pacman']}"
    print(f"  {cmd}")

def show_dependency_error():
    """
    Mostra uma mensagem de erro sobre dependências faltando.
    Usa zenity se disponível, caso contrário usa stderr.
    """
    error_msg = (
        "Dependências obrigatórias não estão instaladas.\n"
        "Verifique a saída do terminal para instruções de instalação.\n"
        "O aplicativo será encerrado."
    )
    
    # Tenta usar zenity para mostrar uma caixa de diálogo
    zenity_path = shutil.which("zenity")
    if zenity_path:
        try:
            subprocess.run([
                zenity_path, "--error",
                "--title=Erro de Dependências",
                f"--text={error_msg}"
            ])
            return
        except Exception:
            pass
    
    # Fallback para stderr
    print(error_msg, file=sys.stderr) 
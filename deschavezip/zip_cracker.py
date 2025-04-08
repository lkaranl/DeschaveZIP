#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zipfile
import time
import os
import tempfile
import struct
import subprocess
import shutil
from pathlib import Path
import sys

class ZipCracker:
    def __init__(self, zip_path, wordlist_path):
        self.zip_path = zip_path
        self.wordlist_path = wordlist_path
        self.is_running = False
        self.callback = None
        self.current_password = 0
        self.total_passwords = 0
        self.password_found = None
        self._7z_binary = self._find_7z_binary()
        self.found_password = None
        self.encryption_type = None
    
    def _find_7z_binary(self):
        """Encontra o caminho para o binário 7z no sistema"""
        # Lista de caminhos possíveis para o binário 7z
        possible_paths = [
            "/usr/bin/7z",
            "/usr/local/bin/7z", 
            "/usr/bin/7za",
            "/usr/local/bin/7za",
            "/opt/homebrew/bin/7z",  # macOS Homebrew
            "/opt/local/bin/7z",     # macOS MacPorts
        ]
        
        # Caminhos para Windows
        windows_paths = [
            "C:\\Program Files\\7-Zip\\7z.exe",
            "C:\\Program Files (x86)\\7-Zip\\7z.exe",
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "7-Zip", "7z.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "7-Zip", "7z.exe")
        ]
        
        # Adicionar caminhos do Windows se estiver no Windows
        if sys.platform.startswith("win"):
            possible_paths.extend(windows_paths)
        
        # Verificar cada caminho
        for path in possible_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
                
        # Tenta encontrar pelo comando which/where
        try:
            if sys.platform.startswith("win"):
                result = subprocess.run(["where", "7z.exe"], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().split("\n")[0]
            else:
                result = subprocess.run(["which", "7z"], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
        except Exception:
            pass
            
        return None
    
    def detect_encryption_type(self):
        """
        Detecta o tipo de criptografia usado no arquivo ZIP
        
        Returns:
            dict: Informações sobre a criptografia do arquivo
        """
        result = {
            "is_encrypted": False,
            "encryption_type": "Nenhuma",
            "supported": True,
            "encrypted_files": 0,
            "total_files": 0,
            "files_info": [],
            "has_external_support": bool(self._7z_binary)  # Se 7z está disponível
        }
        
        try:
            with open(self.zip_path, 'rb') as f:
                data = f.read()
                
            # Verificação básica via zipfile
            with zipfile.ZipFile(self.zip_path) as zip_file:
                result["total_files"] = len(zip_file.infolist())
                
                for zip_info in zip_file.infolist():
                    file_info = {
                        "name": zip_info.filename,
                        "size": zip_info.file_size,
                        "encrypted": False,
                        "encryption_type": "Nenhuma",
                        "compression": self._get_compression_name(zip_info.compress_type)
                    }
                    
                    # Verificar flag de criptografia
                    if zip_info.flag_bits & 0x1:
                        result["is_encrypted"] = True
                        result["encrypted_files"] += 1
                        file_info["encrypted"] = True
                        
                        # Verificar tipo de criptografia analisando cabeçalhos
                        offset = data.find(zip_info.filename.encode())
                        if offset != -1:
                            # Verificar forte indicação de AES
                            if self._check_aes_encryption(zip_file):
                                file_info["encryption_type"] = "AES"
                                result["encryption_type"] = "AES (Avançada)"
                                # AES é suportado se temos 7z
                                result["supported"] = bool(self._7z_binary)
                            else:
                                file_info["encryption_type"] = "ZipCrypto"
                                result["encryption_type"] = "ZipCrypto (Padrão)"
                    
                    result["files_info"].append(file_info)
            
            # Se algum arquivo estiver criptografado com AES, marcamos todo o ZIP como AES
            if any(info["encryption_type"] == "AES" for info in result["files_info"]):
                result["encryption_type"] = "AES (Avançada)"
                result["supported"] = bool(self._7z_binary)
            elif result["is_encrypted"]:
                result["encryption_type"] = "ZipCrypto (Padrão)"
                
            return result
        except Exception as e:
            result["error"] = str(e)
            return result
    
    def _check_aes_encryption(self, zf):
        """
        Verifica se o arquivo ZIP usa criptografia AES
        Implementa verificação avançada para diferentes marcadores AES
        """
        # Leitura dos primeiros bytes para verificar marcadores AES
        with open(self.zip_path, 'rb') as f:
            # Leitura de um trecho maior para análise (até 10KB)
            header_data = f.read(10240)
            
            # Procurar por marcadores comuns de AES em arquivos ZIP
            aes_markers = [
                b"\x01\x99\x07\x00",  # WinZip AES marker
                b"AES",               # Texto "AES" nos cabeçalhos
                b"WinZip",            # Marcador WinZip (geralmente usa AES)
                b"PKZIP"              # Marcador PKZIP (pode usar AES)
            ]
            
            for marker in aes_markers:
                if marker in header_data:
                    return "AES (detectado por assinatura)"
        
        # Verificação pela informação do arquivo ZIP
        for info in zf.infolist():
            if info.flag_bits & 0x1:  # Arquivo está criptografado
                # Verificar campo de compressão estendida (bit 3)
                if info.flag_bits & 0x8:
                    return "AES (detectado por flags)"
                
                # Verificar o campo de criador para PKZIP 5.0 ou superior
                creator_version = info.create_version
                if creator_version >= 50 and info.compress_type == 99:
                    return "AES (detectado por versão do criador)"
        
        return "Padrão ZipCrypto"
    
    def _get_compression_name(self, compress_type):
        """Retorna o nome do tipo de compressão"""
        compression_types = {
            zipfile.ZIP_STORED: "Store (Sem compressão)",
            zipfile.ZIP_DEFLATED: "Deflate",
            zipfile.ZIP_BZIP2: "BZip2",
            zipfile.ZIP_LZMA: "LZMA"
        }
        return compression_types.get(compress_type, "Desconhecido")
    
    def crack_password_with_7z(self, password, zip_path=None):
        """Tenta quebrar a senha com o 7-Zip"""
        if self._7z_binary is None:
            return False, "7-Zip não encontrado no sistema"
            
        if zip_path is None:
            zip_path = self.zip_path
            
        # Calcular timeout adaptativo baseado no tamanho do arquivo
        file_size_kb = os.path.getsize(zip_path) / 1024
        base_timeout = 5  # segundos
        
        # Ajustar timeout com base no tamanho
        if file_size_kb > 10000:  # > 10MB
            adaptive_timeout = base_timeout * 3  # 15 segundos
        elif file_size_kb > 1000:  # > 1MB
            adaptive_timeout = base_timeout * 2  # 10 segundos
        else:
            adaptive_timeout = base_timeout  # 5 segundos
            
        # Garantir que o timeout nunca seja menor que o mínimo seguro
        timeout = max(adaptive_timeout, 5)
            
        try:
            # Usando p7zip para testar a senha
            cmd = [self._7z_binary, "t", "-p" + password, zip_path]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                
                # Verificar resultado
                success_markers = [
                    "Everything is Ok",
                    "Tudo está Ok"  # Versão em português
                ]
                
                error_markers = [
                    "Wrong password",
                    "ERROR: Wrong password",
                    "Data Error",
                    "ERRORS:",
                    "Senha incorreta",  # Versão em português
                    "ERRO: Senha incorreta"  # Versão em português
                ]
                
                for marker in success_markers:
                    if marker in stdout:
                        return True, None
                        
                for marker in error_markers:
                    if marker in stdout or marker in stderr:
                        return False, f"Senha incorreta: {password}"
                
                # Se não encontrou nenhum dos marcadores conhecidos
                return False, f"Resultado não reconhecido do 7z ao testar senha: {password}"
                
            except subprocess.TimeoutExpired:
                process.kill()
                return False, f"Timeout ao testar senha com 7-Zip: {password}"
                
        except Exception as e:
            return False, f"Erro ao usar 7-Zip: {str(e)}"
    
    def crack_password(self, pause_check=None, cancel_check=None):
        """
        Tenta quebrar a senha do arquivo ZIP usando um ataque de dicionário.
        
        Args:
            pause_check: Função que retorna True se o processo deve ser pausado
            cancel_check: Função que retorna True se o processo deve ser cancelado
            
        Yields:
            Um dicionário com o progresso da operação:
            - current_password: Número da senha atual
            - current_text: Texto da senha atual
            - password: A senha encontrada (apenas quando encontrada)
        """
        self.current_password = 0
        self.found_password = None
        
        try:
            # Verificar se o arquivo ZIP existe
            if not os.path.exists(self.zip_path):
                yield {
                    "current_password": 0,
                    "current_text": "",
                    "error": f"Arquivo ZIP não encontrado: {self.zip_path}"
                }
                return
                
            # Verificar se a wordlist existe
            if not os.path.exists(self.wordlist_path):
                yield {
                    "current_password": 0,
                    "current_text": "",
                    "error": f"Wordlist não encontrada: {self.wordlist_path}"
                }
                return
            
            # Detectar o tipo de criptografia
            encryption_info = self.detect_encryption_type()
            if not encryption_info["is_encrypted"]:
                yield {
                    "current_password": 0, 
                    "current_text": "",
                    "error": "O arquivo ZIP não está protegido por senha."
                }
                return
            
            # Verificar se é AES e se temos suporte externo
            is_aes = encryption_info["encryption_type"].startswith("AES")
            has_7z = bool(self._7z_binary)
            
            # Avisar sobre criptografia
            if is_aes:
                if has_7z:
                    yield {
                        "current_password": 0,
                        "current_text": "",
                        "info": f"Arquivo com criptografia {encryption_info['encryption_type']} detectada. Usando 7-Zip para quebra de senha.",
                        "encryption_info": encryption_info
                    }
                else:
                    yield {
                        "current_password": 0,
                        "current_text": "",
                        "warning": f"AVISO: O arquivo usa criptografia {encryption_info['encryption_type']} e 7-Zip não encontrado. A quebra de senha pode falhar.",
                        "encryption_info": encryption_info
                    }
            
            # Se for AES e não temos 7z, tentar usar o método padrão com zipfile (pode falhar)
            # Tentar abrir o arquivo ZIP
            try:
                zip_file = zipfile.ZipFile(self.zip_path)
            except zipfile.BadZipFile:
                yield {
                    "current_password": 0,
                    "current_text": "",
                    "error": "Arquivo ZIP inválido ou corrompido."
                }
                return
            except Exception as e:
                yield {
                    "current_password": 0,
                    "current_text": "",
                    "error": f"Erro ao abrir arquivo ZIP: {str(e)}"
                }
                return
            
            # Verificar se há arquivos no ZIP
            files_to_check = [info for info in zip_file.infolist() if info.file_size > 0]
            if not files_to_check:
                yield {
                    "current_password": 0,
                    "current_text": "",
                    "error": "O arquivo ZIP não contém arquivos para extrair."
                }
                return
            
            # Carregar senhas da wordlist
            passwords = []
            with open(self.wordlist_path, "r", errors="ignore") as wordlist:
                passwords = [line.strip() for line in wordlist if line.strip()]
            
            if not passwords:
                yield {
                    "current_password": 0,
                    "current_text": "",
                    "error": "A wordlist está vazia ou não contém senhas válidas."
                }
                return
                
            yield {
                "current_password": 0,
                "current_text": "",
                "info": f"Testando {len(passwords)} senhas da wordlist..."
            }
            
            # Testar cada senha
            for idx, password in enumerate(passwords):
                # Verificar pausas e cancelamentos
                if pause_check and pause_check():
                    while pause_check():
                        time.sleep(0.1)
                        if cancel_check and cancel_check():
                            return
                
                if cancel_check and cancel_check():
                    return
                
                self.current_password = idx + 1
                
                yield {
                    "current_password": self.current_password,
                    "current_text": password
                }
                
                # Se for AES e temos 7z disponível, usar o 7z para testar a senha
                if is_aes and has_7z:
                    if self.crack_password_with_7z(password):
                        self.found_password = password
                        yield {
                            "current_password": self.current_password,
                            "current_text": password,
                            "password": password,
                            "method": "7z"
                        }
                        return
                    continue
                
                # Diferentes formatos de senha e codificações
                password_formats = [
                    # String original
                    password,
                    # Com diferentes codificações
                    password.encode('utf-8'),
                    password.encode('latin1'),
                    password.encode('ascii', errors='ignore'),
                    password.encode('cp1252', errors='ignore'),
                    # Variações comuns
                    password.lower(),
                    password.upper(),
                    # Remover espaços
                    password.strip(),
                ]
                
                # Testar todas as variações da senha
                for pwd_format in password_formats:
                    # Tenta ler cada arquivo no ZIP
                    for zip_info in files_to_check:
                        try:
                            # Método 1: Tentar ler o arquivo
                            try:
                                zip_file.read(zip_info.filename, pwd=pwd_format if isinstance(pwd_format, bytes) else pwd_format.encode('utf-8', errors='ignore'))
                                # Senha correta encontrada!
                                self.found_password = password
                                yield {
                                    "current_password": self.current_password,
                                    "current_text": password,
                                    "password": password,
                                    "method": "zipfile"
                                }
                                return
                            except RuntimeError as e:
                                # Senha incorreta ou outro erro
                                if not "password required" in str(e) and not "Bad password" in str(e):
                                    # Erro diferente de senha incorreta
                                    continue
                            except zipfile.BadZipFile:
                                # Arquivo corrompido ou formato não suportado
                                continue
                            except Exception:
                                # Outro erro, tentar próximo formato
                                continue
                        except Exception:
                            # Erro ao tentar ler, continuar para próximo arquivo
                            continue
            
            # Se chegar aqui, nenhuma senha funcionou
            yield {
                "current_password": self.current_password,
                "current_text": "",
                "error": "Nenhuma senha encontrada na wordlist."
            }
            
        except Exception as e:
            yield {
                "current_password": self.current_password,
                "current_text": "",
                "error": f"Erro ao processar arquivo: {str(e)}"
            }
        finally:
            if 'zip_file' in locals():
                zip_file.close() 
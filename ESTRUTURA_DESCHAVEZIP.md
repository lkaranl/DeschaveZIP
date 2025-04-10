# Estrutura do Código DeschaveZIP

Este documento explica a estrutura do código do DeschaveZIP, detalhando cada arquivo e sua função no sistema.

## Estrutura de Arquivos

```
DeschaveZIP/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── zip_cracker.py
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── password_dialog.py
│   │   └── progress_dialog.py
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py
│       └── encryption_utils.py
├── tests/
│   ├── __init__.py
│   ├── test_zip_cracker.py
│   └── test_encryption_utils.py
├── setup.py
├── requirements.txt
├── README.md
└── run.py
```

## Descrição dos Arquivos

### Arquivos Principais

- `run.py`: Ponto de entrada da aplicação. Responsável por inicializar o GTK e criar a janela principal.
- `setup.py`: Configuração do pacote Python, definindo dependências e metadados do projeto.
- `requirements.txt`: Lista de dependências Python necessárias para o projeto.

### Diretório src/

#### Arquivos Base
- `__init__.py`: Marca o diretório como um pacote Python.
- `main.py`: Contém a lógica principal da aplicação, incluindo a inicialização e configuração do GTK.
- `zip_cracker.py`: Implementa a lógica de quebra de senhas ZIP, incluindo suporte para ZipCrypto e AES.

#### Diretório gui/
Contém todos os componentes da interface gráfica:
- `main_window.py`: Define a janela principal da aplicação com todos os widgets GTK.
- `password_dialog.py`: Implementa o diálogo para exibição da senha encontrada.
- `progress_dialog.py`: Gerencia a exibição do progresso durante a quebra de senha.

#### Diretório utils/
Contém utilitários auxiliares:
- `file_utils.py`: Funções para manipulação de arquivos e diretórios.
- `encryption_utils.py`: Funções específicas para detecção e manipulação de criptografia.

### Diretório tests/
Contém os testes unitários e de integração:
- `test_zip_cracker.py`: Testes para a lógica de quebra de senhas.
- `test_encryption_utils.py`: Testes para as funções de criptografia.

## Fluxo de Execução

1. O usuário executa `run.py`
2. `run.py` inicializa o GTK e cria a janela principal
3. O usuário seleciona um arquivo ZIP e uma wordlist
4. `zip_cracker.py` analisa o arquivo e determina o tipo de criptografia
5. A quebra de senha é iniciada usando threads paralelas
6. O progresso é atualizado através de `progress_dialog.py`
7. Quando a senha é encontrada, `password_dialog.py` é exibido

## Componentes Principais

### Interface Gráfica (gui/)
- Utiliza GTK 4 para uma interface moderna
- Implementa padrões de design responsivo
- Gerencia eventos e atualizações de UI de forma assíncrona

### Quebra de Senhas (zip_cracker.py)
- Suporta dois métodos de criptografia:
  - ZipCrypto (nativo)
  - AES (via 7-Zip)
- Implementa processamento paralelo
- Gerencia threads e recursos de forma eficiente

### Utilitários (utils/)
- Fornece funções auxiliares para:
  - Manipulação de arquivos
  - Detecção de criptografia
  - Validação de dados
  - Gerenciamento de recursos

## Dependências Externas

- GTK 4: Framework de interface gráfica
- 7-Zip: Necessário para quebra de senhas AES
- Python 3.6+: Linguagem base do projeto
- PyGObject: Bindings Python para GTK 

# DeschaveZIP

Uma ferramenta para quebra de senhas de arquivos ZIP com interface GNOME moderna. Utiliza ataque de dicionário para testar senhas em arquivos ZIP protegidos.

## Funcionalidades

- Interface gráfica moderna baseada em GTK
- Seleção de arquivo ZIP e wordlist com navegador de arquivos gráfico
- Exibição de progresso em tempo real
- Possibilidade de pausar e cancelar o processo
- Logs detalhados da operação

## Aviso Legal

Esta ferramenta foi desenvolvida apenas para fins educacionais e de teste. O uso para quebrar senhas de arquivos sem autorização do proprietário é ilegal.

## Requisitos

- Python 3.6+
- PyGObject (GTK)
- GTK 4.0 ou superior
- Zenity (para o seletor de arquivos gráfico)
- Outras dependências listadas em requirements.txt

## Instalação

### Instalação das dependências (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-4.0 zenity
```

Se disponível, instale também o libadwaita para uma interface mais moderna:

```bash
sudo apt-get install gir1.2-adw-1
```

### Instalação do aplicativo

Clone o repositório:

```bash
git clone https://github.com/usuario/deschavezip.git
cd deschavezip
```

Instale diretamente do diretório:

```bash
pip3 install -e .
```

## Uso

### Executando o aplicativo

Após a instalação, você pode executar o aplicativo de duas formas:

1. Diretamente do diretório do projeto:

```bash
python3 run.py
```

2. Usando o comando instalado (se você instalou com pip):

```bash
deschavezip
```

### Como usar

1. Clique em "Selecionar arquivo ZIP" para abrir o navegador de arquivos e escolher o arquivo protegido
2. Clique em "Selecionar wordlist" para escolher o arquivo de dicionário de senhas
3. Clique em "Iniciar" para começar o processo de quebra
4. Use "Pausar" ou "Cancelar" para controlar o processo

### Criando um arquivo ZIP protegido para testes

Para testar a aplicação, você pode criar facilmente um arquivo ZIP protegido por senha:

#### No Linux/Mac (usando zip na linha de comando):

```bash
# Criar alguns arquivos de texto para teste
echo "Conteúdo de teste 1" > arquivo1.txt
echo "Conteúdo de teste 2" > arquivo2.txt

# Criar o arquivo ZIP com senha
zip -e arquivos_teste.zip arquivo1.txt arquivo2.txt
```

O comando pedirá que você digite e confirme uma senha.

#### No Windows (usando aplicativos como 7-Zip, WinRAR, etc.):

1. Instale o 7-Zip (https://www.7-zip.org/)
2. Selecione os arquivos que deseja comprimir
3. Clique com o botão direito e selecione "7-Zip > Adicionar ao arquivo..."
4. Na janela que se abre, defina uma senha no campo "Senha"
5. Clique em "OK" para criar o arquivo ZIP protegido

## Resolução de Problemas

### Seleção de arquivos

O aplicativo usa o Zenity para exibir um seletor de arquivos gráfico. Se o Zenity não estiver disponível no seu sistema, o aplicativo exibirá automaticamente uma caixa de diálogo alternativa onde você pode digitar manualmente o caminho do arquivo.

Para instalar o Zenity:
```bash
sudo apt-get install zenity
```

### Compatibilidade com diferentes versões do GTK

O aplicativo foi adaptado para funcionar em diferentes versões do GTK 4.x. Para usuários de sistemas mais antigos ou com dificuldades de compatibilidade, a interface oferece mecanismos alternativos para garantir a funcionalidade básica.

### Wordlist de exemplo

O diretório `exemplos` contém uma wordlist de exemplo com senhas comuns que pode ser usada para testes. Essa lista inclui a senha "123" que você pode usar para testar com um arquivo ZIP protegido por essa senha.

### Arquivo de teste incluído

Para facilitar os testes, o repositório inclui um arquivo ZIP protegido com senha no diretório `testes`:

- Arquivo: `testes/arquivo_teste.zip`
- Senha: `123`

Você pode usar este arquivo para verificar se a aplicação está funcionando corretamente.

### Tipos de Criptografia em Arquivos ZIP

O DeschaveZIP pode detectar dois tipos principais de criptografia em arquivos ZIP:

1. **ZipCrypto (Padrão)** - Este é o método tradicional de criptografia de arquivos ZIP, suportado amplamente por todas as ferramentas. O DeschaveZIP consegue quebrar senhas deste tipo de criptografia sem problemas usando o método interno do Python.

2. **AES (Avançada)** - Este é um método mais recente e seguro, geralmente usado em ferramentas como WinZip, 7-Zip e outras aplicações modernas. Para quebrar senhas de arquivos protegidos com AES, o DeschaveZIP utiliza o 7-Zip como ferramenta externa.

Quando um arquivo é analisado, o DeschaveZIP informa o tipo de criptografia detectado e utiliza o método mais adequado para quebrar a senha.

### Requisito para Arquivos AES

Para quebrar senhas de arquivos com criptografia AES, é necessário ter o 7-Zip instalado em seu sistema. Você pode instalá-lo com o comando:

```bash
# Ubuntu/Debian
sudo apt-get install p7zip-full

# Fedora
sudo dnf install p7zip p7zip-plugins

# Arch Linux
sudo pacman -S p7zip
```

O DeschaveZIP detectará automaticamente a instalação do 7-Zip e o utilizará quando necessário para quebrar senhas de arquivos AES.

### Problemas comuns

- **Erro ao selecionar arquivo**: Verifique se o caminho do arquivo não contém caracteres especiais.
- **Senha não encontrada**: Verifique se a senha realmente está na wordlist e se o formato do arquivo ZIP é compatível.
- **Aplicativo fecha inesperadamente**: Verifique os requisitos de instalação do GTK4 e dependências.

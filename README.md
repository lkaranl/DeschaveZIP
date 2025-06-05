# DeschaveZIP

Uma ferramenta para quebra de senhas de arquivos ZIP com interface GNOME. Utiliza ataque de dicionário e processamento paralelo para testar senhas em arquivos ZIP protegidos.

## Funcionalidades

- Interface gráfica moderna baseada em GTK
- Detecção automática do tipo de criptografia (ZipCrypto ou AES)
- Processamento paralelo com múltiplas threads para quebra rápida
- Suporte a criptografia AES através do 7-Zip
- Seleção de arquivo ZIP e wordlist com navegador de arquivos gráfico
- Exibição de progresso em tempo real
- Possibilidade de pausar e cancelar o processo
- Logs detalhados da operação

## Aviso Legal

Esta ferramenta foi desenvolvida apenas para fins educacionais e de teste. O uso para quebrar senhas de arquivos sem autorização do proprietário é ilegal e antiético. O desenvolvedor não se responsabiliza pelo uso indevido desta aplicação.

## Como Funciona - Aspectos Técnicos

### Teoria da Quebra de Senhas em Arquivos ZIP

O DeschaveZIP implementa um **ataque de dicionário** contra arquivos ZIP protegidos por senha. Este método funciona da seguinte forma:

1. **Identificação do Tipo de Criptografia**:
   - Análise dos cabeçalhos binários do arquivo ZIP para determinar se usa ZipCrypto (método tradicional) ou AES (Advanced Encryption Standard)
   - Decodificação dos flags de bits no cabeçalho para detectar criptografia (bit 0x1) 
   - Busca por marcadores específicos (como 0x9901) que indicam criptografia AES

2. **Processo de Quebra para ZipCrypto**:
   - Utiliza a biblioteca nativa `zipfile` do Python
   - Tenta abrir o arquivo protegido com cada senha da wordlist
   - Testa múltiplas codificações (UTF-8, Latin1, ASCII) para lidar com caracteres especiais
   - Verifica se o CRC32 dos dados descomprimidos é válido para confirmar a senha correta

3. **Processo de Quebra para AES**:
   - Utiliza o executável 7-Zip como ferramenta externa
   - Implementa verificação em duas etapas:
     a. Tenta listar o conteúdo do arquivo usando `7z t -p<senha> arquivo.zip`
     b. Tenta extrair pelo menos um arquivo para confirmar que a senha está correta
   - Verifica mensagens específicas de erro/sucesso como "Everything is Ok" ou "Wrong password"

4. **Processamento Paralelo**:
   - Implementa um sistema de threads para testar múltiplas senhas simultaneamente
   - Utiliza ThreadPoolExecutor para gerenciar as threads de forma eficiente
   - Coordena o acesso ao arquivo ZIP através de locks para evitar corrupção
   - Implementa fila de progresso assíncrona para reportar avanço em tempo real

5. **Verificação de Senha Correta**:
   - Para ZipCrypto: conseguir descomprimir o arquivo e verificar CRC32
   - Para AES: extração real de pelo menos um arquivo para verificar a integridade

### Formulação Matemática e Algoritmos

Esta seção descreve em detalhes os algoritmos matemáticos por trás da criptografia e do processo de quebra de senhas em arquivos ZIP.

#### ZipCrypto (PKZIP Tradicional)

O algoritmo ZipCrypto tradicional (desenvolvido para o PKZIP) baseia-se em um gerador de números pseudoaleatórios (PRNG) que utiliza três registradores de 32 bits chamados chaves. A sequência de inicialização das chaves é:

```
key0 = 0x12345678
key1 = 0x23456789
key2 = 0x34567890
```

Para cada byte da senha, o estado das chaves é atualizado:

```
key0 = crc32(key0, byte)
key1 = (key1 + (key0 & 0xFF)) * 0x08088405 + 1
key2 = crc32(key2, key1 >> 24)
```

Onde crc32() implementa um algoritmo CRC32 específico. O processo de criptografia gera um byte de keystream para cada byte de dados:

```
temp = key2 | 2
keystream_byte = (temp * (temp ^ 1)) >> 8
```

A decifragem ocorre pela operação XOR:

```
plaintext = ciphertext ^ keystream_byte
```

#### Vulnerabilidade conhecida como "Known-plaintext attack"

Uma característica que torna o ZipCrypto vulnerável é que os primeiros 12 bytes do arquivo encriptado contêm informações previsíveis:

1. O cabeçalho local do arquivo ZIP inclui um valor de verificação (checksum)
2. Parte desse cabeçalho é encriptada com a sequência de keystream

Esta previsibilidade permite um ataque conhecido como "Known-plaintext attack", que pode ser representado pela equação:

```
P_i ⊕ K_i = C_i
```

Onde:
- P_i é o byte de texto simples (plaintext) conhecido
- K_i é o byte de keystream (desconhecido)
- C_i é o byte cifrado (ciphertext) observado

Como P_i é conhecido e C_i é observado, K_i pode ser determinado:

```
K_i = P_i ⊕ C_i
```

Conhecendo suficientes bytes de keystream, é possível inferir informações sobre a senha.

#### AES (Advanced Encryption Standard)

O AES usado em arquivos ZIP modernos implementa o algoritmo Rijndael com tamanho de bloco de 128 bits e chaves de 128, 192 ou 256 bits. A cifra AES se baseia em quatro operações principais:

1. **SubBytes**: Substituição não-linear de bytes usando uma tabela S-box
2. **ShiftRows**: Operação de transposição onde as linhas são deslocadas ciclicamente
3. **MixColumns**: Mistura das colunas usando multiplicação no campo finito GF(2^8)
4. **AddRoundKey**: Adição de chave por operação XOR

A cifra AES pode ser representada matematicamente como uma série de transformações em uma matriz de estado 4×4 bytes:

```
SubBytes(state[i,j]) = S-box[state[i,j]]

ShiftRows(state[i,j]) = state[i,(j+i)%4]

MixColumns: Cada coluna é multiplicada por uma matriz fixa
| 2 3 1 1 |
| 1 2 3 1 |
| 1 1 2 3 |
| 3 1 1 2 |
no campo finito GF(2^8)

AddRoundKey(state[i,j]) = state[i,j] ⊕ roundKey[i,j]
```

#### Complexidade Computacional e Estimativas de Tempo

A eficiência do ataque de dicionário pode ser expressa pela seguinte fórmula:

```
T = N * t
```

Onde:
- T é o tempo total para testar todas as senhas
- N é o número de senhas na wordlist
- t é o tempo médio para testar cada senha

Com processamento paralelo utilizando P threads, o tempo estimado se torna:

```
T_paralelo = (N * t) / P
```

Para o algoritmo ZipCrypto, o tempo t é principalmente influenciado pela inicialização do estado do PRNG:

```
t_ZipCrypto ≈ c_1 * L + c_2
```

Onde:
- L é o comprimento da senha
- c_1 e c_2 são constantes dependentes do hardware

Para o AES, o tempo é significativamente maior devido à natureza mais complexa do algoritmo:

```
t_AES ≈ c_3 * (10 + r) * L + c_4
```

Onde:
- r é o número de rounds adicionais além dos 10 padrão (0 para AES-128, 2 para AES-192, 4 para AES-256)
- c_3 e c_4 são constantes dependentes do hardware

#### Probabilidade de Sucesso do Ataque de Dicionário

A probabilidade de sucesso de um ataque de dicionário pode ser modelada como:

```
P(sucesso) = |D ∩ S| / |S|
```

Onde:
- D é o conjunto de senhas na wordlist
- S é o espaço de todas as possíveis senhas
- |D ∩ S| representa o número de senhas que estão tanto na wordlist quanto no espaço de possíveis senhas reais
- |S| é o tamanho do espaço de senhas possíveis

Dado que um usuário típico tende a escolher senhas dentro de um subconjunto muito menor do espaço total possível, a estratégia de usar wordlists com senhas comuns ou contextuais pode aumentar significativamente a probabilidade de sucesso.

### Limitações Técnicas

- **ZipCrypto**: Implementa um algoritmo mais antigo e tem vulnerabilidades conhecidas
- **AES**: Mais seguro, mas requer ferramentas externas como 7-Zip

## Requisitos

- Python 3.6+
- PyGObject (GTK)
- GTK 4.0 ou superior
- Zenity (para o seletor de arquivos gráfico)
- 7-Zip (para quebra de senhas em arquivos com criptografia AES)
- Outras dependências listadas em requirements.txt

## Instalação

### Ubuntu/Debian

Instale as dependências do sistema:

```bash
# Instalar GTK e dependências
sudo apt-get update
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-4.0 zenity

# Instalar 7-Zip (necessário para arquivos com criptografia AES)
sudo apt-get install p7zip-full

# Instalar libadwaita para interface mais moderna (opcional)
sudo apt-get install gir1.2-adw-1
```

Clone e instale a aplicação:

```bash
# Clonar o repositório
git clone https://github.com/usuario/deschavezip.git
cd deschavezip

# Instalar via pip (modo desenvolvimento)
pip3 install -e .

# OU instalar diretamente
python3 setup.py install
```

### Fedora

```bash
# Instalar GTK e dependências
sudo dnf install python3-gobject gtk4-devel zenity

# Instalar 7-Zip (necessário para arquivos com criptografia AES)
sudo dnf install p7zip p7zip-plugins

# Instalar libadwaita para interface mais moderna (opcional)
sudo dnf install libadwaita-devel
```

Seguir os mesmos passos de clone e instalação acima.

### Arch Linux

```bash
# Instalar GTK e dependências
sudo pacman -S python-gobject gtk4 zenity

# Instalar 7-Zip (necessário para arquivos com criptografia AES)
sudo pacman -S p7zip

# Instalar libadwaita para interface mais moderna (opcional)
sudo pacman -S libadwaita
```

Seguir os mesmos passos de clone e instalação acima.

## Como Usar

### Executando o Aplicativo

Após a instalação, você pode executar o aplicativo de duas formas:

1. Diretamente do diretório do projeto:

```bash
python3 main.py
```

2. Usando o comando instalado (se você instalou com pip):

```bash
deschavezip
```

### Passo a Passo de Uso

1. **Selecionar o Arquivo ZIP**:
   - Clique no botão "Selecionar arquivo ZIP"
   - Navegue até o arquivo ZIP protegido por senha
   - O sistema exibirá informações sobre o arquivo (tamanho, tipo de criptografia)

2. **Selecionar a Wordlist**:
   - Clique no botão "Selecionar wordlist"
   - Escolha um arquivo de texto contendo uma senha por linha
   - Use wordlists especializadas para o tipo de alvo (corporativo, pessoal, etc.)

3. **Iniciar o Processo**:
   - Clique no botão "Iniciar" para começar a quebra de senha
   - O progresso será mostrado em tempo real
   - Você pode pausar ou cancelar o processo a qualquer momento

4. **Verificar Resultados**:
   - Se uma senha for encontrada, será exibida de forma destacada
   - Em caso de falha, uma mensagem informará que nenhuma senha na wordlist funcionou

### Dicas para Wordlists Eficientes

- Combine várias wordlists para maior cobertura
- Considere criar wordlists personalizadas com base em informações conhecidas sobre o criador do arquivo

## Tipos de Criptografia Suportados

O DeschaveZIP suporta dois tipos principais de criptografia em arquivos ZIP:

### ZipCrypto (Padrão)

Este é o método tradicional de criptografia em arquivos ZIP, desenvolvido originalmente para o formato PKZIP. Pontos importantes:

- Suportado nativamente pelo Python através da biblioteca `zipfile`
- Implementa um algoritmo proprietário baseado em CRC32
- Considerado menos seguro por especialistas modernos em criptografia
- Mais rápido de quebrar devido às suas limitações criptográficas
- Não requer ferramentas externas para ser quebrado

### AES (Advanced Encryption Standard)

Método de criptografia mais recente e seguro, geralmente encontrado em arquivos criados por ferramentas modernas:

- Implementa o padrão AES com chaves de 128, 192 ou 256 bits
- Significativamente mais seguro que o ZipCrypto
- Requer o 7-Zip para ser quebrado (não suportado nativamente pelo Python)
- Mais lento para testar cada senha devido ao algoritmo mais robusto
- Comumente encontrado em arquivos criados pelo WinZip, 7-Zip ou versões recentes de compactadores

## Resolução de Problemas

### Problemas com a Interface Gráfica

- Se o GTK não estiver instalado corretamente, verifique com `pkg-config --modversion gtk4`
- Em sistemas mais antigos, pode ser necessário usar `sudo apt install libgtk-4-dev`

### Problemas com Arquivos AES

- Verifique se o 7-Zip está instalado e acessível no PATH com `which 7z` ou `7z --help`
- Se o 7-Zip estiver instalado mas não for detectado, verifique as permissões de execução

### Problemas de Desempenho

- O número de threads é automaticamente configurado com base no número de CPUs
- Para ajustar manualmente, edite a variável `self.max_workers` no arquivo `zip_cracker.py`
- Wordlists muito grandes podem causar uso excessivo de memória

### Wordlist de exemplo

O diretório `exemplos` contém uma wordlist de exemplo com senhas comuns que pode ser usada para testes. Essa lista inclui a senha "123" que você pode usar para testar com um arquivo ZIP protegido por essa senha.

### Arquivo de teste incluído

Para facilitar os testes, o repositório inclui um arquivo ZIP protegido com senha no diretório `testes`:

- Arquivo: `testes/arquivo_teste.zip`
- Senha: `123`

Você pode usar este arquivo para verificar se a aplicação está funcionando corretamente.

## Contribuições

Contribuições são bem-vindas! Se você gostaria de melhorar o DeschaveZIP:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b minha-nova-feature`)
3. Faça commit das suas mudanças (`git commit -am 'Adicionando nova feature'`)
4. Envie para a branch (`git push origin minha-nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

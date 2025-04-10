# Detalhamento: Quebra de Senhas em Arquivos ZIP

## 1. Estrutura Básica do ZIP

### Formato de Arquivo
Um arquivo ZIP é composto por quatro partes principais:

1. **Cabeçalho Local (Local File Header)**
   - Contém metadados sobre cada arquivo
   - Inclui nome do arquivo, tamanho, método de compressão
   - Localizado no início de cada arquivo dentro do ZIP

   **Exemplo de Cabeçalho Local:**
   ```
   Offset  Tamanho  Descrição
   0       4        Assinatura (0x04034b50)
   4       2        Versão necessária para extração
   6       2        Flags gerais de bits
   8       2        Método de compressão
   10      2        Hora da última modificação
   12      2        Data da última modificação
   14      4        CRC-32
   18      4        Tamanho comprimido
   22      4        Tamanho não comprimido
   26      2        Tamanho do nome do arquivo
   28      2        Tamanho do campo extra
   30      n        Nome do arquivo
   30+n    m        Campo extra
   ```

   **Exemplo Prático:**
   ```
   Arquivo: documento.txt
   Assinatura: 0x04034b50
   Versão: 20 (2.0)
   Flags: 0x0001 (criptografado)
   Método: 8 (deflate)
   CRC-32: 0x12345678
   Tamanho comprimido: 1024 bytes
   Tamanho original: 2048 bytes
   Nome: "documento.txt" (13 bytes)
   ```

2. **Dados Comprimidos**
   - Conteúdo real do arquivo após compressão
   - Pode estar criptografado se protegido por senha
   - Tamanho variável dependendo do método de compressão

   **Exemplo de Dados Comprimidos:**
   ```
   Arquivo original: "Hello World!"
   Comprimido (deflate): 0x4b 0x48 0x4c 0x4a 0x06 0x00
   ```

3. **Cabeçalho Central (Central Directory)**
   - Índice de todos os arquivos no ZIP
   - Contém ponteiros para os cabeçalhos locais
   - Permite acesso rápido a qualquer arquivo

   **Exemplo de Cabeçalho Central:**
   ```
   Offset  Tamanho  Descrição
   0       4        Assinatura (0x02014b50)
   4       2        Versão feita por
   6       2        Versão necessária
   8       2        Flags gerais
   10      2        Método de compressão
   12      2        Hora da última modificação
   14      2        Data da última modificação
   16      4        CRC-32
   20      4        Tamanho comprimido
   24      4        Tamanho não comprimido
   28      2        Tamanho do nome do arquivo
   30      2        Tamanho do campo extra
   32      2        Tamanho do comentário
   34      2        Número do disco inicial
   36      2        Atributos internos
   38      4        Atributos externos
   42      4        Offset do cabeçalho local
   46      n        Nome do arquivo
   46+n    m        Campo extra
   46+n+m  k        Comentário
   ```

4. **Comentário Final (End of Central Directory)**
   - Marca o fim do arquivo ZIP
   - Contém informações sobre o diretório central
   - Inclui offset do início do diretório central

   **Exemplo de Comentário Final:**
   ```
   Offset  Tamanho  Descrição
   0       4        Assinatura (0x06054b50)
   4       2        Número do disco
   6       2        Número do disco do diretório central
   8       2        Entradas neste disco
   10      2        Total de entradas
   12      4        Tamanho do diretório central
   16      4        Offset do diretório central
   20      2        Tamanho do comentário
   22      n        Comentário
   ```

### Proteção por Senha
A proteção por senha em arquivos ZIP pode ser implementada de duas formas:

1. **Criptografia dos Dados**
   - Aplicada aos dados comprimidos
   - Não afeta os cabeçalhos
   - Dois métodos principais: ZipCrypto e AES

   **Exemplo de Dados Criptografados:**
   ```
   Dados originais: "Hello World!"
   Comprimidos: 0x4b 0x48 0x4c 0x4a 0x06 0x00
   Criptografados (ZipCrypto): 0x7a 0x3f 0x2d 0x1b 0x45 0x67
   ```

2. **Verificação de Senha**
   - Implementada no cabeçalho do arquivo
   - Usa valores derivados da senha
   - Permite verificação rápida de senha correta

   **Exemplo de Verificação:**
   ```
   Senha: "123"
   Hash derivado: 0x89 0xab 0xcd 0xef
   Valor armazenado: 0x89 0xab 0xcd 0xef
   ```

## 2. Métodos de Criptografia

### ZipCrypto - O Método Tradicional

#### Processo de Criptografia
1. **Inicialização das Chaves**
   - Três registradores de 32 bits (key0, key1, key2)
   - Valores iniciais: 0x12345678, 0x23456789, 0x34567890
   - Atualizados para cada byte da senha

2. **Geração do Keystream**
   - Usa algoritmo CRC32 modificado
   - Gera um byte de keystream para cada byte de dados
   - Operação: `keystream_byte = (temp * (temp ^ 1)) >> 8`

3. **Criptografia dos Dados**
   - XOR entre dados originais e keystream
   - Processo byte a byte
   - Mantém a compressão intacta

#### Vulnerabilidades
1. **Previsibilidade dos Primeiros Bytes**
   - Primeiros 12 bytes contêm informações previsíveis
   - Permite ataque de plaintext conhecido
   - Facilita a recuperação parcial da senha

2. **Ataque de Plaintext Conhecido**
   - Equação: `P_i ⊕ K_i = C_i`
   - P_i: byte de texto simples conhecido
   - K_i: byte de keystream
   - C_i: byte cifrado observado

3. **Recuperação Parcial**
   - Possível recuperar parte da senha
   - Reduz o espaço de busca
   - Acelera o processo de quebra

### AES - O Padrão Moderno

#### Implementação
1. **Cifra de Bloco**
   - Tamanho de bloco: 128 bits
   - Chaves: 128, 192 ou 256 bits
   - Número de rounds: 10, 12 ou 14

2. **Transformações**
   - SubBytes: substituição não-linear
   - ShiftRows: transposição de bytes
   - MixColumns: mistura de colunas
   - AddRoundKey: XOR com chave

3. **Processo de Criptografia**
   - Dados divididos em blocos de 16 bytes
   - Cada bloco passa por múltiplos rounds
   - Chave expandida para cada round

#### Segurança
1. **Resistência a Ataques**
   - Sem vulnerabilidades conhecidas
   - Necessidade de força bruta
   - Tempo de processamento maior

2. **Força Criptográfica**
   - Baseada em princípios matemáticos sólidos
   - Resistente a ataques analíticos
   - Considerada segura para uso geral

## 3. Verificação de Senha

### Processo de Verificação
1. **Derivação de Chaves**
   - Senha convertida em bytes
   - Processamento através de funções de hash
   - Geração de chaves de criptografia

2. **Tentativa de Descriptografia**
   - Aplicação da chave aos dados
   - Verificação do CRC32
   - Tentativa de descompressão

3. **Verificação do CRC32**
   - Valor armazenado no cabeçalho
   - Comparado com CRC32 dos dados descriptografados
   - Indica senha correta se coincidir

### Detecção de Senha Correta
1. **Critérios de Validação**
   - CRC32 válido após descriptografia
   - Dados descomprimíveis
   - Estrutura do arquivo intacta

2. **Processo de Confirmação**
   - Verificação em múltiplas etapas
   - Prevenção de falsos positivos
   - Garantia de integridade dos dados

## 4. Técnicas de Quebra

### Ataque de Dicionário
1. **Wordlists**
   - Listas de senhas comuns
   - Senhas contextuais
   - Combinações de palavras

2. **Otimizações**
   - Processamento paralelo
   - Cache de resultados
   - Priorização de tentativas

### Processo de Quebra
1. **Leitura do Arquivo**
   - Análise da estrutura
   - Identificação do método de criptografia
   - Extração de informações relevantes

2. **Detecção de Criptografia**
   - Análise dos cabeçalhos
   - Identificação de marcadores
   - Determinação do método

3. **Tentativa de Senhas**
   - Carregamento da wordlist
   - Aplicação de cada senha
   - Verificação dos resultados

## 5. Matemática por Trás

### ZipCrypto
1. **Inicialização**
   ```
   key0 = 0x12345678
   key1 = 0x23456789
   key2 = 0x34567890
   ```

2. **Atualização das Chaves**
   ```
   key0 = crc32(key0, byte)
   key1 = (key1 + (key0 & 0xFF)) * 0x08088405 + 1
   key2 = crc32(key2, key1 >> 24)
   ```

3. **Geração do Keystream**
   ```
   temp = key2 | 2
   keystream_byte = (temp * (temp ^ 1)) >> 8
   ```

### AES
1. **Transformações**
   - SubBytes: S-box não-linear
   - ShiftRows: deslocamento circular
   - MixColumns: multiplicação em GF(2^8)
   - AddRoundKey: XOR com chave

2. **Operações Matemáticas**
   - Multiplicação em campo finito
   - Transformações lineares
   - Permutações não-lineares

## 6. Considerações de Segurança

### Limitações do ZipCrypto
1. **Vulnerabilidades**
   - Previsibilidade do keystream
   - Ataques de plaintext conhecido
   - Recuperação parcial possível

2. **Riscos**
   - Senhas fracas facilmente quebráveis
   - Dados parcialmente recuperáveis
   - Necessidade de senhas fortes

### Força do AES
1. **Segurança**
   - Resistente a ataques analíticos
   - Necessidade de força bruta
   - Tempo de processamento maior

2. **Recomendações**
   - Uso preferencial sobre ZipCrypto
   - Senhas longas e complexas
   - Combinação com outros métodos de segurança

## 7. Conclusão

### Pontos Principais
1. Dois métodos principais de criptografia
2. Vulnerabilidades conhecidas no ZipCrypto
3. Necessidade de força bruta para AES
4. Importância da escolha de senhas fortes
5. Limitações das técnicas de quebra

### Recomendações Finais
1. Uso de AES para proteção
2. Senhas longas e complexas
3. Consciência das limitações
4. Atualização regular de senhas
5. Backup seguro dos dados 

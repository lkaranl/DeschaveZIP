# Como o DeschaveZIP Funciona - Explicação Simples

Imagine que você tem um cofre (arquivo ZIP) que está trancado com uma senha. O DeschaveZIP é como um especialista em abrir cofres, mas de forma legal e ética. Vamos entender como ele funciona:

## 1. O Arquivo ZIP é como um Cofre

Um arquivo ZIP é como um cofre que guarda seus documentos. Quando você coloca uma senha nele, é como se colocasse um cadeado especial. Existem dois tipos principais de "cadeados":

- **ZipCrypto**: É como um cadeado antigo, mais simples
- **AES**: É como um cadeado moderno, mais seguro

## 2. Como o Programa Descobre a Senha

O programa não adivinha a senha. Ele usa uma lista de senhas possíveis (chamada de "wordlist") e tenta uma por uma. É como se ele tivesse um monte de chaves e fosse tentando cada uma até encontrar a que abre o cofre.

### O Processo em Etapas:

1. **Escolha do Arquivo**: Você diz qual arquivo ZIP quer abrir
2. **Análise do Cadeado**: O programa olha o arquivo e descobre que tipo de "cadeado" ele tem
3. **Tentativa de Abertura**: 
   - Se for um cadeado antigo (ZipCrypto), ele tenta abrir diretamente
   - Se for um cadeado moderno (AES), ele usa o 7-Zip para ajudar

## 3. Como Funciona a Quebra de Senha

### Para Cadeados Antigos (ZipCrypto):
- O programa tenta abrir o arquivo com cada senha da lista
- É como tentar várias chaves em um cadeado
- Quando a chave certa é encontrada, o arquivo abre

### Para Cadeados Modernos (AES):
- O programa usa o 7-Zip (um programa especial) para tentar abrir
- É como ter um especialista ajudando a tentar as chaves
- O processo é mais lento, mas mais seguro

## 4. Processamento Paralelo - Trabalhando Rápido

O programa não tenta uma senha por vez. Ele usa várias "pessoas" (chamadas de threads) tentando senhas diferentes ao mesmo tempo. É como ter várias pessoas tentando abrir o cofre ao mesmo tempo, cada uma com uma chave diferente.

## 5. Interface Gráfica - A Parte que Você Vê

A tela do programa mostra:
- Qual arquivo está sendo aberto
- Quantas senhas já foram tentadas
- Quanto tempo já passou
- Se a senha foi encontrada

## 6. O Que Acontece Quando a Senha é Encontrada

Quando o programa encontra a senha certa:
- Ele mostra um aviso na tela
- Mostra qual era a senha
- Você pode usar essa senha para abrir o arquivo

## 7. Importante Saber

- O programa só funciona se a senha estiver na lista que você forneceu
- Quanto mais senhas na lista, maior a chance de encontrar
- O tempo que leva depende de:
  - Quantas senhas tem na lista
  - Que tipo de "cadeado" o arquivo tem
  - Quão forte é seu computador

## 8. Por que Alguns Arquivos São Mais Difíceis de Abrir?

Arquivos com o "cadeado" AES são mais difíceis porque:
- Usam um sistema de proteção mais moderno
- Cada tentativa de senha leva mais tempo
- Precisam de um programa especial (7-Zip) para ajudar

## 9. Dicas para Usar Melhor

- Use listas de senhas (wordlists) boas
- Se souber algo sobre a senha (como palavras que podem estar nela), use isso
- Tenha paciência, especialmente com arquivos grandes
- Lembre-se: o programa só funciona se a senha estiver na lista que você deu 

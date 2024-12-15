# Sistemas Embarcados: Comunicação Cliente-Servidor em TCP

Este projeto consiste em uma implementação de comunicação cliente-servidor utilizando o protocolo TCP, projetada para ser aplicada em sistemas embarcados. A comunicação permite a troca de mensagens estruturadas entre dispositivos, viabilizando sua integração em aplicações reais, como monitoramento remoto, controle de dispositivos e sistemas distribuídos.

## Estrutura do Projeto

A estrutura do projeto segue a divisão lógica de arquivos, organizada da seguinte forma:

```
project-root/
├── include/    # Contém os arquivos de cabeçalho (.h)
├── src/        # Contém os arquivos de implementação em C++ (.cpp)
└── scripts/    # Contém scripts auxiliares e códigos Python (.py)
```

## Recursos Principais

- **Servidor TCP:** Implementado em Python para maior flexibilidade e simplicidade.
- **Cliente TCP:** Desenvolvido em C++ para integração com sistemas embarcados.
- **Mensagens Estruturadas:** Suporte para envio de mensagens com cabeçalhos e payloads configuráveis.
- **Expansibilidade:** Estrutura modular para facilitar a adição de novas funcionalidades.

## Pré-requisitos

Antes de executar este projeto, certifique-se de ter os seguintes itens instalados:

- Compilador C++ (compatível com C++11 ou superior)
- Python 3.x
- Bibliotecas adicionais (especifique aqui caso necessário, como `struct`, `socket`, etc.)

## Como Rodar os Códigos

### Cliente (C++)

1. Compile os arquivos:
   Para x86_64
   ```bash
   make ARCH=x86_64 
   ```
   Para arm
   ```bash
   make ARCH=arm
   ```

3. Execute o cliente:
4. Para x86_64
   ```bash
   make run ARCH=x84_64
   ```
   Para arm
    ```bash
   make run ARCH=arm
   ```

### Servidor (Python)

1. Navegue para a pasta `scripts`:
   ```bash
   cd scripts
   ```

2. Execute o servidor:
   ```bash
   python3 running_server.py
   ```
### Client (Python)

1. Navegue para a pasta `scripts`:
   ```bash
   cd scripts
   ```

2. Execute o servidor:
   ```bash
   python3 running_client.py
   ```

## Exemplos de Uso

Descreva aqui exemplos de execução do sistema, incluindo:

Após iniciar o servidor e os clientes, você pode então executar comandos base como troca de peer digitando no terminal /change_peer nome_do_peer. 
Também é possível trocar o id do cliente usando o comando /change_id novo_nome

## Expansões Futuras

- Suporte a criptografia de mensagens.
- Implementação de protocolo para controle de fluxo.
- Criar novos tipos de mensagens para aplicações diversas.

## Contribuição

Contribuições são bem-vindas! Para contribuir.

Autores:
Eduardo Morelli Fares
Clarice Viegas Lira
Andre Victor Kovalski
Juan Thomas de Lima Bueno
Gabriel Silva Madeira
Caio Martinez Roberto da Silva
Guilherme Rebecchi dos Santos
Felipe Mendes Bortolozo


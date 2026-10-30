# AT03 – Calculadora distribuída via RMI (Pyro5)

Trabalho AT03 de Sistemas Distribuídos (SMD/UFC, 2026). É a versão em Python do projeto `ExemploRMI`, feita com **Pyro5** (Python Remote Objects), que o enunciado aceita como alternativa ao Java RMI.

## Paradigma

Invocação remota de métodos (RMI): o cliente chama `calc.soma(10, 15)` como se fosse um objeto local. Quem cuida da rede é o proxy.

| Java RMI | Pyro5 neste projeto |
|---|---|
| Interface que estende `Remote` | `@Pyro5.api.expose` na classe `Calculadora` |
| Objeto remoto (`UnicastRemoteObject`) | instância de `Calculadora` registrada no `Daemon` |
| `rmiregistry` | Name Server do Pyro (`python -m Pyro5.nameserver`, porta 9090) |
| `Naming.rebind("nome", obj)` | `ns.register("calculadora.remota", uri)` |
| `Naming.lookup("nome")` → stub | `Proxy("PYRONAME:calculadora.remota")` → proxy |
| `RemoteException` / exceção remota | a exceção do servidor é relançada no cliente |

Métodos remotos: `soma`, `subtracao`, `multiplicacao`, `divisao` e `calcular_expressao`. Uma divisão por zero lança `ZeroDivisionError` no servidor, o Pyro serializa a exceção e o proxy a relança no cliente, que a trata.

O daemon usa a **porta fixa 5001**. Sem isso o Pyro sorteia uma porta a cada execução, e o filtro do Wireshark não funcionaria.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `calculadora.py` | Objeto remoto (≈ interface + implementação do Java) |
| `servidor.py` | Cria o daemon, exporta o objeto e registra no Name Server |
| `cliente.py` | Faz o lookup, obtém o proxy e mostra o menu |
| `expressao.py` | Parser de expressões (descida recursiva, sem `eval`) |
| `test_expressao.py` | Testes do parser |

Todas as linhas de `calculadora.py`, `servidor.py` e `cliente.py` estão comentadas.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Como executar

Em três terminais, nesta ordem:

```bash
python -m Pyro5.nameserver       # 1. Name Server (≈ rmiregistry) em localhost:9090
python servidor.py               # 2. daemon na porta 5001 e registro de "calculadora.remota"
python cliente.py                # 3. lookup no Name Server e menu
```

Opções: `servidor.py --porta 5001 --ns-host localhost --ns-porta 9090` e `cliente.py --ns-host localhost --ns-porta 9090`.

O menu é igual ao das outras calculadoras. No **Modo A**, o cliente faz o parsing e chama um método remoto por operação (`→ servidor: soma(10, 15) = 25`). No **Modo B**, faz uma única chamada a `calcular_expressao`.

Testes do parser: `python -m pytest -q` (ou `python -m unittest`).

## Captura no Wireshark

1. Interface de loopback: **Adapter for loopback traffic capture** no Windows (Npcap), `lo` no Linux, `lo0` no macOS.
2. Filtro: `tcp.port == 9090 or tcp.port == 5001`
3. Comece a captura antes de abrir o cliente.

O que observar:
- primeiro, uma conexão na **porta 9090**: o cliente pergunta ao Name Server qual URI corresponde a `calculadora.remota` (é o lookup);
- depois, uma conexão na **porta 5001**, direto com o daemon, por onde passam todas as invocações;
- o conteúdo é binário (protocolo do Pyro com serialização *serpent*), mas os nomes dos métodos (`soma`, `divisao`...) e os valores aparecem legíveis no payload;
- no Modo A há uma ida e volta por operação, e no Modo B uma só.

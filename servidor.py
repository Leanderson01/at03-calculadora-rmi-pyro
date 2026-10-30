"""
Servidor da calculadora via RMI (Pyro5).

Analogia com Java RMI:
  - Name Server do Pyro (python -m Pyro5.nameserver, porta 9090) ≈ rmiregistry
  - Daemon.register(objeto)   ≈ UnicastRemoteObject.exportObject(objeto)
  - ns.register(nome, uri)    ≈ Naming.rebind(nome, objeto)
  - daemon.requestLoop()      ≈ a JVM ficar viva atendendo chamadas

Antes de rodar este servidor, suba o Name Server:
    python -m Pyro5.nameserver
"""

import argparse  # lê host e portas da linha de comando

import Pyro5.api  # biblioteca de objetos remotos (RMI) para Python

from calculadora import Calculadora  # classe do objeto remoto

NOME_REGISTRADO = "calculadora.remota"  # nome lógico pelo qual os clientes acham o objeto (≈ nome no rmiregistry)


def main():  # ponto de entrada do servidor
    parser = argparse.ArgumentParser(description="Servidor da calculadora via Pyro5 (RMI)")  # define os argumentos
    parser.add_argument("--host", default="localhost", help="endereço do daemon")  # host onde o objeto fica acessível
    parser.add_argument("--porta", type=int, default=5001, help="porta fixa do daemon (padrão 5001)")  # porta fixa facilita o filtro no Wireshark
    parser.add_argument("--ns-host", default="localhost", help="host do Name Server")  # onde está o "rmiregistry"
    parser.add_argument("--ns-porta", type=int, default=9090, help="porta do Name Server (padrão 9090)")  # porta padrão do Name Server
    args = parser.parse_args()  # lê os argumentos digitados

    daemon = Pyro5.api.Daemon(host=args.host, port=args.porta)  # cria o daemon: o servidor de rede que recebe as chamadas remotas
    uri = daemon.register(Calculadora(), objectId="calculadora")  # exporta o objeto e obtém sua URI (≈ exportObject do Java)
    print(f"Objeto remoto exportado: {uri}")  # mostra a URI PYRO:calculadora@host:5001

    try:  # o Name Server pode não estar no ar
        ns = Pyro5.api.locate_ns(host=args.ns_host, port=args.ns_porta)  # obtém um proxy para o Name Server (≈ LocateRegistry.getRegistry)
    except Pyro5.errors.NamingError:  # não achou o Name Server
        print(f"Name Server não encontrado em {args.ns_host}:{args.ns_porta}. Rode antes: python -m Pyro5.nameserver")  # orienta o usuário
        daemon.close()  # libera a porta do daemon
        return  # encerra sem traceback

    ns.register(NOME_REGISTRADO, uri)  # associa o nome à URI no Name Server (≈ Naming.rebind)
    print(f"Registrado no Name Server como '{NOME_REGISTRADO}'. Aguardando chamadas (Ctrl+C para sair)")  # avisa que está pronto

    try:  # laço principal; Ctrl+C encerra
        daemon.requestLoop()  # bloqueia atendendo chamadas remotas indefinidamente
    except KeyboardInterrupt:  # o usuário apertou Ctrl+C
        print("\nEncerrando servidor.")  # mensagem de saída
    finally:  # sempre executa
        try:  # o Name Server pode ter caído antes do servidor
            ns.remove(NOME_REGISTRADO)  # tira o nome do registro (≈ Naming.unbind)
        except Pyro5.errors.CommunicationError:  # Name Server inacessível
            pass  # nada a desfazer
        daemon.close()  # fecha o daemon e libera a porta 5001


if __name__ == "__main__":  # só executa main() quando o arquivo é rodado diretamente
    main()  # inicia o servidor

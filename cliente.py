"""
Cliente da calculadora via RMI (Pyro5).

O cliente pede ao Name Server o objeto "calculadora.remota" e recebe um
proxy (≈ stub do Java RMI). Chamar proxy.soma(10, 15) parece uma chamada
local, mas o proxy serializa os argumentos, envia ao daemon na porta 5001,
espera a resposta e devolve o resultado — ou relança a exceção remota.
"""

import argparse  # lê o endereço do Name Server da linha de comando

import Pyro5.api  # biblioteca de objetos remotos (RMI) para Python
import Pyro5.errors  # exceções de comunicação do Pyro

from expressao import SIMBOLOS, ErroExpressao, analisar_operacao_simples, avaliar, formatar  # parser próprio

NOME_REGISTRADO = "calculadora.remota"  # nome usado pelo servidor no Name Server


def executor_remoto(calc):  # cria o executor do Modo A, ligado ao proxy
    def executar(op, a, b):  # chamado pelo parser para cada operação básica
        metodo = getattr(calc, op)  # pega o método remoto pelo nome (ex.: calc.soma)
        resultado = metodo(a, b)  # invocação remota: ida e volta ao servidor
        print(f"  → servidor: {op}({formatar(a)}, {formatar(b)}) = {formatar(resultado)}")  # mostra cada chamada remota
        return resultado  # devolve o valor para o parser continuar
    return executar  # o parser recebe essa função como executor


MENU = """
=== Calculadora RMI (Pyro5) ===
1) Operação simples (ex: 10 + 15)
2) Expressão – Modo A (cliente decompõe e chama o servidor por operação)
3) Expressão – Modo B (servidor calcula a expressão inteira)
0) Sair"""  # texto do menu


def main():  # ponto de entrada do cliente
    parser = argparse.ArgumentParser(description="Cliente da calculadora via Pyro5 (RMI)")  # define os argumentos
    parser.add_argument("--ns-host", default="localhost", help="host do Name Server")  # onde está o "rmiregistry"
    parser.add_argument("--ns-porta", type=int, default=9090, help="porta do Name Server (padrão 9090)")  # porta padrão
    args = parser.parse_args()  # lê os argumentos digitados

    uri = f"PYRONAME:{NOME_REGISTRADO}@{args.ns_host}:{args.ns_porta}"  # URI lógica: resolve o nome no Name Server (≈ Naming.lookup)
    calc = Pyro5.api.Proxy(uri)  # cria o proxy (≈ stub); a conexão é aberta na primeira chamada
    try:  # testa a conexão antes de mostrar o menu
        calc._pyroBind()  # consulta o Name Server, obtém a URI real e conecta no daemon (porta 5001)
    except Pyro5.errors.CommunicationError as e:  # Name Server ou servidor fora do ar
        print(f"Não foi possível conectar à calculadora remota: {e}")  # explica o problema
        return  # encerra sem traceback
    except Pyro5.errors.NamingError as e:  # o nome não está registrado
        print(f"Objeto '{NOME_REGISTRADO}' não encontrado no Name Server: {e}")  # o servidor não foi iniciado
        return  # encerra sem traceback

    print(f"Conectado ao objeto remoto {calc._pyroUri}")  # mostra a URI real do objeto
    try:  # garante liberar o proxy no final
        while True:  # repete o menu até o usuário sair
            print(MENU)  # mostra as opções
            opcao = input("Escolha: ").strip()  # lê a opção digitada
            if opcao == "0":  # sair
                break  # sai do laço
            if opcao not in ("1", "2", "3"):  # opção inexistente
                print("Opção inválida.")  # avisa e mostra o menu de novo
                continue  # volta ao início do laço
            texto = input("Digite: ").strip()  # lê a operação ou expressão
            try:  # erros de entrada ou exceções remotas não encerram o programa
                if opcao == "1":  # operação simples
                    op, a, b = analisar_operacao_simples(texto)  # extrai operação e operandos
                    resultado = getattr(calc, op)(a, b)  # uma única invocação remota
                    print(f"{formatar(a)} {SIMBOLOS[op]} {formatar(b)} = {formatar(resultado)}")  # mostra o resultado
                elif opcao == "2":  # Modo A
                    resultado = avaliar(texto, executor_remoto(calc))  # parser local + uma invocação remota por operação
                    print(f"Resultado final: {formatar(resultado)}")  # mostra o resultado
                else:  # Modo B
                    resultado = calc.calcular_expressao(texto)  # uma invocação remota com a expressão inteira
                    print(f"Resultado (calculado no servidor): {formatar(resultado)}")  # mostra o resultado
            except ErroExpressao as e:  # o parser local recusou a entrada
                print(f"Entrada inválida: {e}")  # explica o erro
            except ZeroDivisionError as e:  # exceção lançada no servidor e relançada aqui pelo proxy
                print(f"Erro remoto: {e}")  # mostra a mensagem que veio do servidor
            except ValueError as e:  # expressão inválida detectada no servidor (Modo B)
                print(f"Erro remoto: {e}")  # mostra a mensagem que veio do servidor
    except (KeyboardInterrupt, EOFError):  # Ctrl+C ou fim da entrada
        print()  # pula linha antes de sair
    except Pyro5.errors.CommunicationError as e:  # o servidor caiu no meio da sessão
        print(f"Conexão perdida: {e}")  # avisa o usuário
    finally:  # sempre executa
        calc._pyroRelease()  # fecha a conexão do proxy com o daemon
        print("Até logo!")  # despedida


if __name__ == "__main__":  # só executa main() quando o arquivo é rodado diretamente
    main()  # inicia o cliente

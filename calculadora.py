"""
Objeto remoto da calculadora (equivalente à interface + implementação do
ExemploRMI em Java).

Em Java RMI teríamos:
  - uma interface que estende java.rmi.Remote, declarando os métodos;
  - uma classe que implementa essa interface e é exportada
    (UnicastRemoteObject).

No Pyro5 não existe interface separada: o decorador @expose marca quais
métodos podem ser chamados remotamente — ele cumpre o papel da interface
Remote. O resto da classe é Python comum.
"""

import Pyro5.api  # biblioteca de objetos remotos (RMI) para Python

from expressao import ErroExpressao, avaliar, executor_local  # parser próprio (sem eval)


@Pyro5.api.expose  # torna os métodos públicos desta classe chamáveis pela rede (≈ interface Remote do Java)
class Calculadora:  # classe do objeto remoto (≈ classe que implementa a interface remota em Java)
    def soma(self, a, b):  # método remoto: soma
        print(f"    chamada remota: soma({a}, {b})")  # registra a chamada no console do servidor
        return executor_local("soma", float(a), float(b))  # calcula localmente e devolve ao cliente

    def subtracao(self, a, b):  # método remoto: subtração
        print(f"    chamada remota: subtracao({a}, {b})")  # registra a chamada no console do servidor
        return executor_local("subtracao", float(a), float(b))  # calcula localmente e devolve ao cliente

    def multiplicacao(self, a, b):  # método remoto: multiplicação
        print(f"    chamada remota: multiplicacao({a}, {b})")  # registra a chamada no console do servidor
        return executor_local("multiplicacao", float(a), float(b))  # calcula localmente e devolve ao cliente

    def divisao(self, a, b):  # método remoto: divisão
        print(f"    chamada remota: divisao({a}, {b})")  # registra a chamada no console do servidor
        return executor_local("divisao", float(a), float(b))  # b == 0 lança ZeroDivisionError, que o Pyro leva até o cliente

    def calcular_expressao(self, expr):  # método remoto do Modo B: o servidor calcula a expressão inteira
        print(f"    chamada remota: calcular_expressao({expr!r})")  # registra a chamada no console do servidor
        try:  # traduz o erro do parser para uma exceção que o cliente conhece
            return avaliar(str(expr), executor_local)  # parser + executor local, tudo no servidor
        except ErroExpressao as e:  # ErroExpressao é uma classe nossa, que o Pyro não sabe recriar no cliente
            raise ValueError(f"Expressão inválida: {e}") from None  # ValueError é embutida e chega intacta ao cliente

from abc import ABC, abstractmethod


class MarketplaceBase(ABC):
    """
    Contrato base para integrações com marketplaces.

    Cada marketplace deverá implementar:
    - autenticação
    - consulta de pedidos
    - consulta de pedido específico
    - normalização dos dados para o padrão interno do ERP
    """

    codigo = None
    nome = None

    def __init__(self):
        if not self.codigo:
            raise ValueError(
                "A integração deve definir o código do marketplace."
            )

        if not self.nome:
            raise ValueError(
                "A integração deve definir o nome do marketplace."
            )

    @abstractmethod
    def esta_configurado(self):
        """
        Retorna True quando as configurações mínimas da integração
        estiverem disponíveis.
        """
        raise NotImplementedError

    @abstractmethod
    def listar_pedidos(self, **filtros):
        """
        Consulta pedidos diretamente no marketplace.
        """
        raise NotImplementedError

    @abstractmethod
    def buscar_pedido(self, pedido_externo):
        """
        Consulta um pedido específico pelo identificador externo.
        """
        raise NotImplementedError

    @abstractmethod
    def normalizar_pedido(self, dados):
        """
        Converte a resposta específica do marketplace para
        o padrão interno usado pelo ERP.
        """
        raise NotImplementedError

    def identificar(self):
        return {
            "codigo": self.codigo,
            "nome": self.nome,
            "configurado": self.esta_configurado(),
        }

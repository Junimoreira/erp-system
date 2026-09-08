import os
import base64
import json
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests

from services.marketplaces.base import MarketplaceBase
from database.marketplaces_db import (
    buscar_canal_por_codigo,
    buscar_credenciais_marketplace,
    salvar_credenciais_marketplace,
)


class MagaluMarketplace(MarketplaceBase):
    """
    Integração com a API de pedidos do Magalu.

    As credenciais e tokens nunca devem ser gravados
    diretamente neste arquivo.
    """

    codigo = "MAGALU"
    nome = "Magazine Luiza"

    API_BASE_URL = "https://api.magalu.com"
    AUTH_URL = "https://id.magalu.com/login"
    TOKEN_URL = "https://id.magalu.com/oauth/token"

    SCOPES = (
        "open:order-order-seller:read",
        "open:order-delivery-seller:read",
        "open:order-invoice-seller:read",
        "open:order-logistics-seller:read",

        # Escrita necessaria para faturamento e logistica



    )

    def __init__(
        self,
        access_token=None,
        client_id=None,
        client_secret=None,
        redirect_uri=None,
        timeout=30
    ):
        self.access_token = (
            access_token
            or os.getenv("MAGALU_ACCESS_TOKEN")
        )

        self.client_id = (
            client_id
            or os.getenv("MAGALU_CLIENT_ID")
        )

        self.client_secret = (
            client_secret
            or os.getenv("MAGALU_CLIENT_SECRET")
        )

        self.redirect_uri = (
            redirect_uri
            or os.getenv("MAGALU_REDIRECT_URI")
        )

        self.timeout = int(timeout)

        self.canal_id = None
        self.refresh_token = None
        self.access_token_expira_em = None
        self.tenant_id = None
        self.tenant_nome = None

        super().__init__()

    def _obter_canal_id(self):
        if self.canal_id:
            return self.canal_id

        canal = buscar_canal_por_codigo(
            self.codigo
        )

        if not canal:
            raise RuntimeError(
                "Canal MAGALU nao encontrado no ERP."
            )

        self.canal_id = int(
            canal["id"]
        )

        return self.canal_id

    def carregar_credenciais_banco(self):
        canal_id = self._obter_canal_id()

        credencial = buscar_credenciais_marketplace(
            canal_id
        )

        if not credencial:
            return False

        if not credencial.get("ativo"):
            return False

        self.access_token = (
            credencial.get("access_token")
        )

        self.refresh_token = (
            credencial.get("refresh_token")
        )

        self.access_token_expira_em = (
            credencial.get(
                "access_token_expira_em"
            )
        )

        self.tenant_id = (
            credencial.get(
                "tenant_id"
            )
        )

        self.tenant_nome = (
            credencial.get(
                "tenant_nome"
            )
        )

        return bool(
            str(
                self.access_token or ""
            ).strip()
        )

    @staticmethod
    def _extrair_payload_jwt(token):
        token = str(
            token or ""
        ).strip()

        partes = token.split(".")

        if len(partes) != 3:
            return {}

        try:
            payload_base64 = partes[1]

            padding = (
                "="
                * (
                    -len(payload_base64)
                    % 4
                )
            )

            payload_bytes = (
                base64.urlsafe_b64decode(
                    payload_base64
                    + padding
                )
            )

            payload = json.loads(
                payload_bytes.decode(
                    "utf-8"
                )
            )

            if not isinstance(
                payload,
                dict,
            ):
                return {}

            return payload

        except Exception:
            return {}


    @staticmethod
    def _calcular_expiracao_token(dados):
        expires_in = dados.get(
            "expires_in"
        )

        if expires_in in (
            None,
            "",
        ):
            return None

        try:
            segundos = int(
                expires_in
            )

        except (
            TypeError,
            ValueError,
        ) as erro:
            raise RuntimeError(
                "expires_in retornado pelo "
                "ID Magalu e invalido."
            ) from erro

        if segundos <= 0:
            return datetime.utcnow()

        return (
            datetime.utcnow()
            + timedelta(
                seconds=segundos
            )
        )

    def salvar_resposta_tokens(
        self,
        dados,
        autorizado=False,
        renovacao=False,
    ):
        if not isinstance(
            dados,
            dict,
        ):
            raise ValueError(
                "Resposta de tokens invalida."
            )

        access_token = str(
            dados.get("access_token")
            or ""
        ).strip()

        if not access_token:
            raise RuntimeError(
                "Access token ausente "
                "na resposta do Magalu."
            )

        refresh_token = str(
            dados.get("refresh_token")
            or ""
        ).strip()

        token_type = str(
            dados.get("token_type")
            or "Bearer"
        ).strip()

        payload_token = (
            self._extrair_payload_jwt(
                access_token
            )
        )

        tenant_id = str(
            payload_token.get("sub")
            or dados.get("tenant_id")
            or dados.get("tenant")
            or ""
        ).strip() or None

        tenant_nome = str(
            payload_token.get("tenant_name")
            or payload_token.get("tenant_nome")
            or payload_token.get("organization_name")
            or dados.get("tenant_name")
            or dados.get("tenant_nome")
            or ""
        ).strip() or None

        expiracao = (
            self._calcular_expiracao_token(
                dados
            )
        )

        agora = datetime.utcnow()

        canal_id = self._obter_canal_id()

        credencial_id = (
            salvar_credenciais_marketplace(
                canal_id=canal_id,
                access_token=access_token,
                refresh_token=(
                    refresh_token
                    or None
                ),
                token_type=token_type,
                access_token_expira_em=expiracao,
                autorizado_em=(
                    agora
                    if autorizado
                    else None
                ),
                ultima_renovacao_em=(
                    agora
                    if renovacao
                    else None
                ),
                tenant_id=tenant_id,
                tenant_nome=tenant_nome,
                scopes=dados.get("scope"),
                ativo=True,
            )
        )

        self.access_token = access_token

        if refresh_token:
            self.refresh_token = (
                refresh_token
            )

        self.access_token_expira_em = (
            expiracao
        )

        self.tenant_id = tenant_id
        self.tenant_nome = tenant_nome

        return credencial_id

    def _access_token_precisa_renovar(
        self,
        margem_segundos=5,
    ):
        if not str(
            self.access_token or ""
        ).strip():
            return True

        expiracao = (
            self.access_token_expira_em
        )

        if expiracao is None:
            return False

        limite = (
            datetime.utcnow()
            + timedelta(
                seconds=int(
                    margem_segundos
                )
            )
        )

        return expiracao <= limite

    def garantir_access_token(self):
        if not self.access_token:
            self.carregar_credenciais_banco()

        if not self._access_token_precisa_renovar():
            return self.access_token

        if not self.refresh_token:
            self.carregar_credenciais_banco()

        refresh_token = str(
            self.refresh_token or ""
        ).strip()

        if not refresh_token:
            raise RuntimeError(
                "Refresh token do Magalu "
                "nao esta disponivel."
            )

        dados = self.renovar_access_token(
            refresh_token
        )

        self.salvar_resposta_tokens(
            dados,
            renovacao=True,
        )

        return self.access_token

    def oauth_configurado(self):
        return all(
            str(valor or "").strip()
            for valor in (
                self.client_id,
                self.client_secret,
                self.redirect_uri,
            )
        )

    def gerar_url_autorizacao(self, state):
        if not self.oauth_configurado():
            raise RuntimeError(
                "Configuracao OAuth do Magalu incompleta."
            )

        state = str(state or "").strip()

        if not state:
            raise ValueError(
                "O parametro state e obrigatorio."
            )

        parametros = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.SCOPES),
            "response_type": "code",
            "choose_tenants": "true",
            "state": state,
        }

        return (
            self.AUTH_URL
            + "?"
            + urlencode(parametros)
        )

    def trocar_codigo_por_tokens(self, code):
        if not self.oauth_configurado():
            raise RuntimeError(
                "Configuracao OAuth do Magalu incompleta."
            )

        code = str(code or "").strip()

        if not code:
            raise ValueError(
                "O codigo de autorizacao do Magalu e obrigatorio."
            )

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
            "grant_type": "authorization_code",
        }

        try:
            resposta = requests.post(
                self.TOKEN_URL,
                json=payload,
                timeout=self.timeout,
            )

        except requests.RequestException as erro:
            raise RuntimeError(
                "Falha de comunicacao com o ID Magalu "
                "durante a troca do codigo de autorizacao."
            ) from erro

        if resposta.status_code >= 400:
            raise RuntimeError(
                "O ID Magalu recusou a troca do codigo "
                f"de autorizacao. HTTP {resposta.status_code}."
            )

        try:
            dados = resposta.json()

        except ValueError as erro:
            raise RuntimeError(
                "O ID Magalu retornou uma resposta "
                "que nao e JSON valido."
            ) from erro

        if not isinstance(dados, dict):
            raise RuntimeError(
                "Resposta inesperada do ID Magalu."
            )

        access_token = str(
            dados.get("access_token") or ""
        ).strip()

        if not access_token:
            raise RuntimeError(
                "O ID Magalu nao retornou access_token."
            )

        self.access_token = access_token

        return dados

    def renovar_access_token(self, refresh_token):
        if not self.oauth_configurado():
            raise RuntimeError(
                "Configuracao OAuth do Magalu incompleta."
            )

        refresh_token = str(
            refresh_token or ""
        ).strip()

        if not refresh_token:
            raise ValueError(
                "O refresh token do Magalu e obrigatorio."
            )

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            resposta = requests.post(
                self.TOKEN_URL,
                data=payload,
                timeout=self.timeout,
            )

        except requests.RequestException as erro:
            raise RuntimeError(
                "Falha de comunicacao com o ID Magalu "
                "durante a renovacao do access token."
            ) from erro

        if resposta.status_code >= 400:
            raise RuntimeError(
                "O ID Magalu recusou a renovacao "
                f"do access token. HTTP {resposta.status_code}."
            )

        try:
            dados = resposta.json()

        except ValueError as erro:
            raise RuntimeError(
                "O ID Magalu retornou uma resposta "
                "que nao e JSON valido."
            ) from erro

        if not isinstance(dados, dict):
            raise RuntimeError(
                "Resposta inesperada do ID Magalu."
            )

        access_token = str(
            dados.get("access_token") or ""
        ).strip()

        if not access_token:
            raise RuntimeError(
                "O ID Magalu nao retornou access_token."
            )

        self.access_token = access_token

        return dados

    def esta_configurado(self):
        return bool(
            str(
                self.access_token or ""
            ).strip()
        )

    def _headers(self):
        self.garantir_access_token()

        if not self.esta_configurado():
            raise RuntimeError(
                "Integração Magalu não configurada. "
                "Access token ausente."
            )

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        metodo,
        caminho,
        params=None,
        json=None,
        headers_extra=None,
    ):
        url = (
            self.API_BASE_URL.rstrip("/")
            + "/"
            + caminho.lstrip("/")
        )

        headers = self._headers()

        if headers_extra:
            headers.update(
                headers_extra
            )

        try:
            resposta = requests.request(
                method=metodo,
                url=url,
                headers=headers,
                params=params,
                json=json,
                timeout=self.timeout
            )

        except requests.RequestException as erro:
            raise RuntimeError(
                "Falha de comunicação com a API Magalu: "
                f"{erro}"
            ) from erro

        if resposta.status_code == 401:
            raise RuntimeError(
                "A API Magalu recusou a autenticação. "
                "O token pode estar ausente, inválido ou expirado."
            )

        if resposta.status_code == 403:
            raise RuntimeError(
                "A aplicação não possui permissão suficiente "
                "para este recurso do Magalu."
            )

        if resposta.status_code == 404:
            raise RuntimeError(
                "Recurso não encontrado na API Magalu."
            )

        if resposta.status_code >= 400:
            raise RuntimeError(
                "Erro retornado pela API Magalu. "
                f"HTTP {resposta.status_code}."
            )

        if not resposta.content:
            return None

        try:
            return resposta.json()

        except ValueError as erro:
            raise RuntimeError(
                "A API Magalu retornou uma resposta "
                "que não é JSON válido."
            ) from erro

    def listar_pedidos(self, **filtros):
        params = {
            chave: valor
            for chave, valor in filtros.items()
            if valor is not None
        }

        return self._request(
            metodo="GET",
            caminho="/seller/v1/orders",
            params=params
        )

    def listar_entregas(
        self,
        channel_id,
        **filtros,
    ):
        channel_id = str(
            channel_id or ""
        ).strip()

        if not channel_id:
            raise ValueError(
                "Informe o X-Channel-Id do Magalu."
            )

        params = {
            chave: valor
            for chave, valor in filtros.items()
            if valor is not None
        }

        return self._request(
            metodo="GET",
            caminho="/seller/v1/deliveries",
            params=params,
            headers_extra={
                "X-Channel-Id": channel_id,
            },
        )


    @staticmethod
    def normalizar_codigo_pedido(pedido_externo):
        pedido_externo = str(
            pedido_externo or ""
        ).strip()

        if not pedido_externo:
            raise ValueError(
                "Informe o código do pedido Magalu."
            )

        if pedido_externo.upper().startswith("LU-"):
            pedido_externo = pedido_externo[3:]

        pedido_externo = pedido_externo.strip()

        if not pedido_externo:
            raise ValueError(
                "Código do pedido Magalu inválido."
            )

        return pedido_externo

    def buscar_pedido(self, pedido_externo):
        codigo_pedido = (
            self.normalizar_codigo_pedido(
                pedido_externo
            )
        )

        return self._request(
            metodo="GET",
            caminho=(
                "/seller/v1/orders/"
                + codigo_pedido
            )
        )

    def buscar_entrega(
        self,
        entrega_id,
        channel_id=None,
    ):
        entrega_id = str(
            entrega_id or ""
        ).strip()

        if not entrega_id:
            raise ValueError(
                "Informe o ID da entrega Magalu."
            )

        headers_extra = None

        channel_id = str(
            channel_id or ""
        ).strip()

        if channel_id:
            headers_extra = {
                "X-Channel-Id": channel_id,
            }

        return self._request(
            metodo="GET",
            caminho=(
                "/seller/v1/deliveries/"
                + entrega_id
            ),
            headers_extra=headers_extra,
        )

    def listar_notas_entrega(
        self,
        entrega_id,
        channel_id=None,
    ):
        entrega_id = str(
            entrega_id or ""
        ).strip()

        if not entrega_id:
            raise ValueError(
                "Informe o ID da entrega Magalu."
            )

        headers_extra = None

        channel_id = str(
            channel_id or ""
        ).strip()

        if channel_id:
            headers_extra = {
                "X-Channel-Id": channel_id,
            }

        return self._request(
            metodo="GET",
            caminho=(
                "/seller/v1/deliveries/"
                + entrega_id
                + "/invoices"
            ),
            headers_extra=headers_extra,
        )

    def normalizar_pedido(self, dados):
        """
        A normalização será implementada depois de validarmos
        uma resposta real da API do Magalu.
        """

        if not isinstance(dados, dict):
            raise ValueError(
                "Os dados do pedido Magalu devem ser "
                "um dicionário."
            )

        return dados

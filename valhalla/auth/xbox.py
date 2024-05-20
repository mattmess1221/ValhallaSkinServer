import datetime
import enum
from typing import Any, TypedDict

import httpx

XBOX_AUTH_BASE = "https://{0}.auth.xboxlive.com/{0}/{1}"
XBOX_USER_AUTH = XBOX_AUTH_BASE.format("user", "authenticate")
XBOX_XSTS_AUTH = XBOX_AUTH_BASE.format("xsts", "authorize")

MC_BASE = "https://api.minecraftservices.com/{0}"
MC_AUTH_XBOX = MC_BASE.format("authentication/login_with_xbox")
MC_PROFILE = MC_BASE.format("minecraft/profile")


class XError(enum.IntEnum):
    NO_ACCOUNT = 2148916233
    REGION = 2148916235
    CHILD = 2148916238


x_default_error_message = "Unknown error while authenticating with xbox live"
x_error_messages = {
    XError.NO_ACCOUNT: "This account is not associated with a Xbox Live account.",
    XError.REGION: "This account is in a region where Xbox Live is not available.",
    XError.CHILD: "This account is a child and must be added to a Family.",
}


class XSTSError(TypedDict):
    Identity: str
    XErr: XError
    Message: str
    Redirect: str


def get_x_error_message(err: XSTSError) -> str:
    return x_error_messages.get(err["XErr"], x_default_error_message)


class XboxLoginError(Exception):
    def __init__(self, err: XSTSError):
        super().__init__(get_x_error_message(err))
        self.err = err


class TextureState(enum.StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class SkinVariant(enum.StrEnum):
    CLASSIC = "CLASSIC"
    SLIM = "SLIM"


class Texture(TypedDict):
    id: str
    state: TextureState
    url: str


class Skin(Texture):
    variant: SkinVariant


class Cape(Texture):
    alias: str


class MinecraftProfile(TypedDict):
    id: str
    name: str
    skins: list[Skin]
    capes: list[Cape]


class MinecraftAuth(TypedDict):
    username: str
    roles: list[Any]
    metadata: dict[str, Any]
    access_token: str
    expires_in: int
    token_type: str


class XboxAuth(TypedDict):
    IssueInstant: datetime.datetime
    NotAfter: datetime.datetime
    Token: str
    DisplayClaims: dict[str, list[dict[str, str]]]


async def login_with_xbox(xbl_access_token: str) -> MinecraftProfile:
    async with httpx.AsyncClient() as client:

        async def auth_xboxlive(oauth_token: str) -> XboxAuth:
            response = await client.post(
                XBOX_USER_AUTH,
                json={
                    "Properties": {
                        "AuthMethod": "RPS",
                        "SiteName": "user.auth.xboxlive.com",
                        "RpsTicket": f"d={oauth_token}",
                    },
                    "RelyingParty": "http://auth.xboxlive.com",
                    "TokenType": "JWT",
                },
            )

            return XboxAuth(response.json())

        async def auth_mojang(xbox_auth: XboxAuth) -> XboxAuth:
            response = await client.post(
                XBOX_XSTS_AUTH,
                json={
                    "Properties": {
                        "SandboxId": "RETAIL",
                        "UserTokens": [xbox_auth["Token"]],
                    },
                    "RelyingParty": "rp://api.minecraftservices.com/",
                    "TokenType": "JWT",
                },
            )
            if response.is_client_error:
                raise XboxLoginError(XSTSError(response.json()))

            return XboxAuth(response.json())

        async def auth_minecraft_from_xbox(mojang_auth: XboxAuth) -> MinecraftAuth:
            userhash = mojang_auth["DisplayClaims"]["xui"][0]["uhs"]
            xsts_token = mojang_auth["Token"]
            response = await client.post(
                MC_AUTH_XBOX,
                json={"identityToken": f"XBL3.0 x={userhash};{xsts_token}"},
            )
            data = response.json()

            return MinecraftAuth(data)

        async def get_minecraft_profile(mc_auth: MinecraftAuth) -> MinecraftProfile:
            token_type = mc_auth["token_type"]
            access_token = mc_auth["access_token"]
            response = await client.get(
                MC_PROFILE,
                headers={"Authorization": f"{token_type} {access_token}"},
            )
            return MinecraftProfile(response.json())

        async def login(xbl_access_token: str) -> MinecraftProfile:
            """Start the lengthy authorization process."""
            xauth = await auth_xboxlive(xbl_access_token)
            xsxt = await auth_mojang(xauth)
            mcauth = await auth_minecraft_from_xbox(xsxt)
            return await get_minecraft_profile(mcauth)

        return await login(xbl_access_token)

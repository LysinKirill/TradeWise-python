import logging

import grpc
import jwt

from app.domain.services.IClaimValuesService import IClaimValuesService
from app.infrastructure.GrpcContextAccessor import GrpcContextAccessor

class ClaimValuesService(IClaimValuesService):
    def __init__(
            self,
            context_accessor: GrpcContextAccessor,
            jwt_secret: str
    ):
        self.context_accessor = context_accessor
        self.jwt_secret = jwt_secret

    async def get_email(self) -> str:
        """
        Extracts the user's email from the JWT claims in the gRPC request metadata.
        :return: The user's email as a string.
        """
        context = self.context_accessor.get_context()

        metadata = context.invocation_metadata()
        auth_header = self._get_auth_header(metadata)

        if not auth_header:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Authorization header is missing")

        token = self._extract_jwt_token(auth_header)
        if not token:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid authorization header")

        email = self._decode_jwt_and_get_email(token)
        if not email:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token")

        return email

    def _get_auth_header(self, metadata: list[tuple[str, str]]) -> str | None:
        """
        Extracts the authorization header from the gRPC metadata.
        :param metadata: The gRPC metadata.
        :return: The authorization header value or None if not found.
        """
        for key, value in metadata:
            if key == "authorization":
                return value
        return None

    def _extract_jwt_token(self, auth_header: str) -> str | None:
        """
        Extracts the JWT token from the authorization header.
        :param auth_header: The authorization header value.
        :return: The JWT token or None if the header is invalid.
        """
        if not auth_header.startswith("Bearer "):
            return None
        return auth_header.split(" ")[1]

    def _decode_jwt_and_get_email(self, token: str) -> str | None:
        """
        Decodes the JWT token and extracts the email claim.
        :param token: The JWT token.
        :return: The email claim or None if the token is invalid or expired.
        """
        try:
            decoded = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return decoded.get("email")
        except Exception as e:
            logging.error(e)
            return None
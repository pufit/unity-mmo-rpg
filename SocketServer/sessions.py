from flask.sessions import SecureCookieSessionInterface
from itsdangerous import URLSafeTimedSerializer


class SimpleSecureCookieSessionInterface(SecureCookieSessionInterface):
    def get_signing_serializer(self, secret_key):
        if not secret_key:
            return None
        signer_kwargs = dict(
            key_derivation=self.key_derivation,
            digest_method=self.digest_method
        )
        return URLSafeTimedSerializer(secret_key, salt=self.salt,
                                      serializer=self.serializer,
                                      signer_kwargs=signer_kwargs)


def decode_flask_cookie(secret_key, cookie_value):
    sscsi = SimpleSecureCookieSessionInterface()
    signing_serializer = sscsi.get_signing_serializer(secret_key)
    return signing_serializer.loads(cookie_value)


def encode_flask_cookie(secret_key, cookie_dict):
    sscsi = SimpleSecureCookieSessionInterface()
    signing_serializer = sscsi.get_signing_serializer(secret_key)
    return signing_serializer.dumps(cookie_dict)

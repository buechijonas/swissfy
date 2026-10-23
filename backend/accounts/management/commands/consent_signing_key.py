from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Generates the key pair that signs the consent status handed to govex. "
        "The private key goes into CONSENT_PRIVATE_KEY, the public key to govex."
    )

    def handle(self, *args, **options):
        key = ec.generate_private_key(ec.SECP256R1())
        private = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        public = (
            key.public_key()
            .public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode()
        )
        escaped = private.strip().replace("\n", "\\n")
        self.stdout.write(f'CONSENT_PRIVATE_KEY="{escaped}"\n')
        self.stdout.write("\nPublic key for govex:\n")
        self.stdout.write(public)

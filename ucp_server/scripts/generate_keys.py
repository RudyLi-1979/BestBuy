"""
Script to generate UCP RSA key pair
"""
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os


def generate_keys(private_key_path: str = "./keys/ucp_private.pem", 
                  public_key_path: str = "./keys/ucp_public.pem"):
    """
    Generate RSA key pair for UCP
    
    Args:
        private_key_path: Path to save private key
        public_key_path: Path to save public key
    """
    # Create keys directory if it doesn't exist
    os.makedirs(os.path.dirname(private_key_path), exist_ok=True)
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Save private key
    with open(private_key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        )
    
    # Generate public key
    public_key = private_key.public_key()
    
    # Save public key
    with open(public_key_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )
    
    print(f"✓ Private key saved to: {private_key_path}")
    print(f"✓ Public key saved to: {public_key_path}")


if __name__ == "__main__":
    generate_keys()

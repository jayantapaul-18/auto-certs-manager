import requests
import subprocess
import json
from datetime import datetime, timedelta
from kubernetes import client, config
import logging

# Configuration
NCLM_API_URL = "https://nclm.example.com/api"
NCLM_API_KEY = "your_api_key"
ALLOWED_DOMAINS = ["example.com", "sub.example.com"]
DEFAULT_DOMAIN = "default.example.com"
KUBERNETES_NAMESPACES = ["namespace1", "namespace2"]
STATE_FILE = "cert_state.json"

# Logging Setup
logging.basicConfig(level=logging.DEBUG, filename="cert_manager.log", format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger()

# State Management
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# Certificate Creation
def create_certificate(app_domain_name, sans_in=None):
    if app_domain_name not in ALLOWED_DOMAINS:
        logger.error(f"Domain {app_domain_name} not allowed")
        raise ValueError("Domain not allowed")
    sans = sans_in if sans_in else [DEFAULT_DOMAIN]
    logger.info(f"Creating certificate for {app_domain_name} with SANs {sans}")
    response = requests.post(
        f"{NCLM_API_URL}/certificates",
        headers={"Authorization": f"Bearer {NCLM_API_KEY}"},
        json={"app_domain_name": app_domain_name, "sans": sans}
    )
    response.raise_for_status()
    cert_data = response.json()
    cert_id = cert_data["id"]
    pkcs12_data = download_pkcs12(cert_id)
    pem, cert, key = decode_pkcs12(pkcs12_data)
    state = load_state()
    state[cert_id] = {
        "certificate_name": f"{app_domain_name}-cert",
        "certificate_id": cert_id,
        "type": "public-prod",
        "app_domain_name": app_domain_name,
        "sans": sans,
        "sans_in": sans_in,
        "created_on": datetime.now().isoformat(),
        "expires_on": (datetime.now() + timedelta(days=365)).isoformat(),
        "key": key,
        "cert": cert,
        "rotation_days": 30
    }
    save_state(state)
    upload_to_kubernetes(app_domain_name, cert, key)
    logger.info(f"Certificate {cert_id} created and uploaded")

# Download and Decode
def download_pkcs12(cert_id):
    logger.debug(f"Downloading PKCS12 for cert_id {cert_id}")
    response = requests.get(
        f"{NCLM_API_URL}/certificates/{cert_id}/pkcs12",
        headers={"Authorization": f"Bearer {NCLM_API_KEY}"}
    )
    response.raise_for_status()
    return response.content

def decode_pkcs12(pkcs12_data):
    logger.debug("Decoding PKCS12")
    # Placeholder: Use OpenSSL or cryptography library
    pem = subprocess.check_output(["openssl", "pkcs12", "-in", "-", "-out", "-", "-nodes"], input=pkcs12_data)
    cert = "extracted_cert"  # Extract from PEM
    key = "extracted_key"    # Extract from PEM
    return pem.decode(), cert, key

# Kubernetes Upload
def upload_to_kubernetes(app_domain_name, cert, key):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    secret_name = f"{app_domain_name}-tls"
    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(name=secret_name),
        data={"tls.crt": cert, "tls.key": key}
    )
    for namespace in KUBERNETES_NAMESPACES:
        try:
            v1.create_namespaced_secret(namespace, secret)
            logger.info(f"Secret {secret_name} created in {namespace}")
        except client.exceptions.ApiException as e:
            if e.status == 409:
                v1.replace_namespaced_secret(secret_name, namespace, secret)
                logger.info(f"Secret {secret_name} updated in {namespace}")
            else:
                logger.error(f"Failed to upload secret to {namespace}: {e}")
                raise

# Auto-Renewal
def check_and_renew():
    state = load_state()
    for cert_id, cert_data in state.items():
        expires_on = datetime.fromisoformat(cert_data["expires_on"])
        if expires_on - datetime.now() < timedelta(days=30):
            logger.info(f"Renewing certificate {cert_id}")
            renew_certificate(cert_id)

def renew_certificate(cert_id):
    response = requests.post(
        f"{NCLM_API_URL}/certificates/{cert_id}/renew",
        headers={"Authorization": f"Bearer {NCLM_API_KEY}"}
    )
    response.raise_for_status()
    new_cert_data = response.json()
    new_cert_id = new_cert_data["id"]
    pkcs12_data = download_pkcs12(new_cert_id)
    pem, cert, key = decode_pkcs12(pkcs12_data)
    validate_certificate(cert)
    state = load_state()
    state[new_cert_id] = state.pop(cert_id)
    state[new_cert_id].update({
        "certificate_id": new_cert_id,
        "cert": cert,
        "key": key,
        "rotated_on": datetime.now().isoformat(),
        "expires_on": (datetime.now() + timedelta(days=365)).isoformat()
    })
    save_state(state)
    upload_to_kubernetes(state[new_cert_id]["app_domain_name"], cert, key)
    logger.info(f"Certificate {new_cert_id} renewed and uploaded")

def validate_certificate(cert):
    logger.debug("Validating certificate")
    # Implement validation (e.g., check domain, expiry)

# Additional Operations
def delete_certificate(cert_id):
    logger.info(f"Deleting certificate {cert_id}")
    requests.delete(f"{NCLM_API_URL}/certificates/{cert_id}", headers={"Authorization": f"Bearer {NCLM_API_KEY}"})
    state = load_state()
    state.pop(cert_id, None)
    save_state(state)

def search_certificates(criteria):
    state = load_state()
    results = [cert for cert_id, cert in state.items() if all(cert.get(k) == v for k, v in criteria.items())]
    logger.info(f"Search results: {len(results)} certificates found")
    return results

# Main Loop (e.g., run daily)
if __name__ == "__main__":
    create_certificate("app.example.com", ["san1.example.com"])
    check_and_renew()
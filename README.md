## Automate Certificate Management

Below is a comprehensive solution for creating an automation framework to manage public digital certificates using the NCLM API, tailored to the requirements specified in the query. This solution automates certificate creation, management, renewal, and deployment to Kubernetes environments while maintaining state, logging, and adhering to enterprise standards.

## Automation Framework for Public Digital Certificate Management Using NCLM API

This framework automates the lifecycle of public digital certificates using the NetGuard Certificate Lifecycle Manager (NCLM) API, ensuring seamless creation, renewal, and deployment to Kubernetes environments. Here's how it works:

### Objectives

- **Create Certificates**: Generate certificates via the NCLM API using `app_domain_name` and optional `sans_in` (Subject Alternative Names), defaulting to a configured domain if `sans_in` is not provided.
- **Domain Restrictions**: Limit certificate domains to an approved list, ensuring compatibility with Kubernetes TLS.
- **Download and Decode**: Retrieve certificates in PKCS12 format, decode them into PEM, certificate, and private key files.
- **Manage Certificates**: Track and manage certificates using the NCLM API, including expiration monitoring and auto-renewal 30 days before expiry.
- **Deploy to Kubernetes**: Upload renewed certificates to preconfigured Kubernetes namespaces as secrets, following the naming convention `app_domain_name-tls`.
- **State Management**: Maintain a state file with detailed certificate metadata.
- **Additional Operations**: Support manual renew, delete, and search functionalities.
- **Logging**: Include debug, audit, and error logs.
- **Enterprise Standards**: Adhere to security, compliance, and operational best practices.

---

### Architecture

The framework consists of a central management system that:

- Interacts with the NCLM API for certificate operations.
- Interfaces with Kubernetes clusters to manage secrets.
- Runs periodically to monitor and renew certificates.
- Provides manual operation capabilities via commands or an API.

#### Components

1. **Configuration**: Defines allowed domains, default domain, Kubernetes namespaces, and NCLM API credentials.
2. **Certificate Creation Module**: Handles certificate generation via the NCLM API.
3. **Certificate Download and Decoding Module**: Downloads and decodes PKCS12 files.
4. **Certificate Management Module**: Monitors certificate status and expiration.
5. **Auto-Renewal Module**: Renews certificates and updates Kubernetes secrets.
6. **State Management Module**: Tracks certificate details in a state file.
7. **Operations Module**: Provides renew, delete, and search functionalities.
8. **Logging Module**: Logs all activities for debugging, auditing, and error tracking.

---

### Detailed Solution

#### 1. Configuration

- **Allowed Domains**: A predefined list (e.g., `["example.com", "sub.example.com"]`) restricts certificate creation to authorized domains.
- **Default Domain**: Used when `sans_in` is not provided (e.g., `default.example.com`).
- **Kubernetes Namespaces**: Preconfigured list of namespaces (e.g., `["namespace1", "namespace2"]`) for secret deployment.
- **NCLM API Credentials**: API endpoint and key for authentication.

#### 2. Certificate Creation

- **Input**: `app_domain_name` (required), `sans_in` (optional array of SANs).
- **Process**:
  - Validate `app_domain_name` against the allowed domains list.
  - If `sans_in` is provided, include it in the certificate request; otherwise, use the default domain.
  - Call the NCLM API to create the certificate.
  - Store certificate metadata in the state file.
- **Output**: Certificate ID and details from the NCLM API.

#### 3. Certificate Download and Decoding

- **Process**:
  - Download the certificate in PKCS12 format using the NCLM API.
  - Decode the PKCS12 file using OpenSSL to extract:
    - PEM file (full certificate chain).
    - Certificate (public key).
    - Private key.
- **Tools**: OpenSSL or a library like Python’s `cryptography`.

#### 4. Certificate Management

- **Tracking**: Use the NCLM API to retrieve certificate details, including expiration dates.
- **Monitoring**: Periodically check expiration dates against the state file.
- **Renewal Trigger**: Initiate renewal when a certificate is within 30 days of expiry.

#### 5. Auto-Renewal

- **Process**:
  - Renew the certificate using the NCLM API.
  - Download the new PKCS12 file.
  - Decode it to obtain the new PEM, certificate, and private key.
  - Validate the renewed certificate (e.g., check domain names, expiry).
  - Upload to Kubernetes secrets in all preconfigured namespaces using the naming convention `app_domain_name-tls`.
  - Update the state file with new details (e.g., `rotated_on`, `expires_on`).

#### 6. State Management

- **State File Format**: JSON or database (e.g., SQLite) storing:
  - `certificate_name`: Name of the certificate.
  - `name_in`: Input name (if applicable).
  - `certificate_id`: Unique ID from NCLM API.
  - `type`: Certificate type (e.g., `public-npe`, `public-prod`, `public-multiple-san-prod`).
  - `app_domain_name`: Primary domain.
  - `base_domain`: Base domain (if different).
  - `sans`: List of SANs in the certificate.
  - `sans_in`: Input SANs provided during creation.
  - `rotation_days`: Renewal interval (e.g., 30 days).
  - `created_on`: Creation timestamp.
  - `expires_on`: Expiry timestamp.
  - `rotated_on`: Last renewal timestamp.
  - `key`: Private key (encrypted if stored).
  - `cert`: Certificate content.
  - `renew_id`: ID of the renewed certificate (if applicable).
- **Operations**: Functions to read, update, and save the state file.

#### 7. Additional Operations

- **Renew**: Manually renew a certificate by ID or domain name.
- **Delete**: Remove a certificate from the NCLM API and state file.
- **Search**: Query certificates by criteria (e.g., domain, type, expiration).

#### 8. Logging

- **Debug Logs**: Detailed logs for troubleshooting (e.g., API calls, decoding steps).
- **Audit Logs**: Record all certificate operations (e.g., creation, renewal, deletion).
- **Error Logs**: Capture and report failures (e.g., API errors, Kubernetes upload issues).

### Enterprise Standards and Enhancements

- **Security**:
  - Encrypt sensitive data (e.g., private keys) in the state file.
  - Use secure API authentication (e.g., OAuth tokens).
  - Restrict access to the framework via role-based access control (RBAC).
- **Compliance**: Adhere to standards like GDPR or PCI-DSS if applicable (e.g., audit logs for accountability).
- **Error Handling**: Robustly handle API failures, network issues, or Kubernetes errors with retries and alerts.
- **Scalability**: Support multiple clusters and large certificate volumes using a database instead of a JSON file.
- **Idempotency**: Ensure operations (e.g., secret updates) can be safely retried.
- **Monitoring and Alerts**: Integrate with tools like Prometheus to monitor certificate health and alert on failures.
- **Backup**: Regularly back up the state file and certificate data.
- **Documentation**: Provide detailed usage guides and API docs.
- **Testing**: Include unit, integration, and end-to-end tests.

---

### Workflow Summary

1. **Creation**: Validate domain, create certificate via NCLM API, decode PKCS12, store in state, and upload to Kubernetes.
2. **Monitoring**: Check state file daily for expiring certificates.
3. **Renewal**: Renew certificates 30 days before expiry, validate, update Kubernetes secrets, and refresh state.
4. **Operations**: Manually renew, delete, or search certificates as needed.

This solution ensures efficient, secure, and enterprise-grade management of public digital certificates across Kubernetes environments using the NCLM API.

## Demo

```bash
python3 certs_manager.py
```

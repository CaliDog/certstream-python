<p align="center">
    <img align="center" src="https://user-images.githubusercontent.com/1072598/31840406-1fe37936-b59a-11e7-939a-71d36e584fc9.png">
    <h3 align="center">CertStream-Python</h3>
    <p align="center">See SSL certs as they're issued live.</p>
</p>

**Certstream-python** is a library for interacting with the [certstream network](https://certstream.calidog.io/) to monitor an aggregated feed from a collection of [Certificate Transparency Lists](https://www.certificate-transparency.org/known-logs).

It leverages the excellent 2/3 compatible [websocket-client](https://github.com/websocket-client/websocket-client) library and supports reconnecting automatically. 

# Installing

```
pip install certstream
```

# Usage

Usage is about as simple as it gets, simply import the `certstream` module and register a callback with `certstream.listen_for_events`. Once you register a callback it will be called with 2 arguments - `message`, and `context`. 

```python
import logging
import sys
import datetime
import certstream

def print_callback(message, context):
    logging.debug("Message -> {}".format(message))

    if message['message_type'] == "heartbeat":
        return

    if message['message_type'] == "certificate_update":
        all_domains = message['data']['leaf_cert']['all_domains']

        if len(all_domains) == 0:
            domain = "NULL"
        else:
            domain = all_domains[0]

        sys.stdout.write(u"[{}] {} (SAN: {})\n".format(datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S'), domain, ", ".join(message['data']['leaf_cert']['all_domains'][1:])))
        sys.stdout.flush()

logging.basicConfig(format='[%(levelname)s:%(name)s] %(asctime)s - %(message)s', level=logging.INFO)

certstream.listen_for_events(print_callback)
```

# Example data structure

The data structure coming from CertStream looks like this:

```
{
    "message_type": "certificate_update",
    "data": {
        "update_type": "X509LogEntry",
        "leaf_cert": {
            "subject": {
                "aggregated": "/CN=e-zigarette-liquid-shop.de",
                "C": null,
                "ST": null,
                "L": null,
                "O": null,
                "OU": null,
                "CN": "e-zigarette-liquid-shop.de"
            },
            "extensions": {
                "keyUsage": "Digital Signature, Key Encipherment",
                "extendedKeyUsage": "TLS Web Server Authentication, TLS Web Client Authentication",
                "basicConstraints": "CA:FALSE",
                "subjectKeyIdentifier": "AC:4C:7B:3C:E9:C8:7F:CB:E2:7D:5D:64:F2:25:0C:89:C2:AE:F0:5E",
                "authorityKeyIdentifier": "keyid:A8:4A:6A:63:04:7D:DD:BA:E6:D1:39:B7:A6:45:65:EF:F3:A8:EC:A1\n",
                "authorityInfoAccess": "OCSP - URI:http://ocsp.int-x3.letsencrypt.org\nCA Issuers - URI:http://cert.int-x3.letsencrypt.org/\n",
                "subjectAltName": "DNS:e-zigarette-liquid-shop.de, DNS:www.e-zigarette-liquid-shop.de",
                "certificatePolicies": "Policy: 2.23.140.1.2.1\nPolicy: 1.3.6.1.4.1.44947.1.1.1\n  CPS: http://cps.letsencrypt.org\n  User Notice:\n    Explicit Text: This Certificate may only be relied upon by Relying Parties and only in accordance with the Certificate Policy found at https://letsencrypt.org/repository/\n"
            },
            "not_before": 1508123861.0,
            "not_after": 1515899861.0,
            "as_der": "::BASE64_DER_CERT::",
            "all_domains": [
                "e-zigarette-liquid-shop.de",
                "www.e-zigarette-liquid-shop.de"
            ]
        },
        "chain": [
            {
                "subject": {
                    "aggregated": "/C=US/O=Let's Encrypt/CN=Let's Encrypt Authority X3",
                    "C": "US",
                    "ST": null,
                    "L": null,
                    "O": "Let's Encrypt",
                    "OU": null,
                    "CN": "Let's Encrypt Authority X3"
                },
                "extensions": {
                    "basicConstraints": "CA:TRUE, pathlen:0",
                    "keyUsage": "Digital Signature, Certificate Sign, CRL Sign",
                    "authorityInfoAccess": "OCSP - URI:http://isrg.trustid.ocsp.identrust.com\nCA Issuers - URI:http://apps.identrust.com/roots/dstrootcax3.p7c\n",
                    "authorityKeyIdentifier": "keyid:C4:A7:B1:A4:7B:2C:71:FA:DB:E1:4B:90:75:FF:C4:15:60:85:89:10\n",
                    "certificatePolicies": "Policy: 2.23.140.1.2.1\nPolicy: 1.3.6.1.4.1.44947.1.1.1\n  CPS: http://cps.root-x1.letsencrypt.org\n",
                    "crlDistributionPoints": "\nFull Name:\n  URI:http://crl.identrust.com/DSTROOTCAX3CRL.crl\n",
                    "subjectKeyIdentifier": "A8:4A:6A:63:04:7D:DD:BA:E6:D1:39:B7:A6:45:65:EF:F3:A8:EC:A1"
                },
                "not_before": 1458232846.0,
                "not_after": 1615999246.0,
                "as_der": "::BASE64_DER_CERT::"
            },
            {
                "subject": {
                    "aggregated": "/O=Digital Signature Trust Co./CN=DST Root CA X3",
                    "C": null,
                    "ST": null,
                    "L": null,
                    "O": "Digital Signature Trust Co.",
                    "OU": null,
                    "CN": "DST Root CA X3"
                },
                "extensions": {
                    "basicConstraints": "CA:TRUE",
                    "keyUsage": "Certificate Sign, CRL Sign",
                    "subjectKeyIdentifier": "C4:A7:B1:A4:7B:2C:71:FA:DB:E1:4B:90:75:FF:C4:15:60:85:89:10"
                },
                "not_before": 970348339.0,
                "not_after": 1633010475.0,
                "as_der": "::BASE64_DER_CERT::"
            }
        ],
        "cert_index": 19587936,
        "seen": 1508483726.8601687,
        "source": {
            "url": "mammoth.ct.comodo.com",
            "name": "Comodo 'Mammoth' CT log"
        }
    }
}
```
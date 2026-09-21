# Security policy

## Synthetic data

This repository contains **only synthetic** organizational data. Do not commit real risk registers, customer data, credentials, webhook URLs, API keys, or model secrets.

## Reporting

If you find a vulnerability in the demo application or an accidental secret in git history, open a private GitHub security advisory on this repository. Do not file a public issue that includes secrets.

## Operational expectations for reuse

If you adapt this schema for a real organization:

- Treat residual-risk rationales as sensitive management information.
- Restrict database access.
- Do not expose Streamlit Community Cloud apps that contain live enterprise data.
- Keep human approval separate from model output.

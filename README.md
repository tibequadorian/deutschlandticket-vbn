**Public Infrastructure, Public Code**

This program can download your mobile tickets from VBN without the need for a proprietary app.

# Installation

*(Recommended)* Create a virtual environment using `venv`:
```
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:
```
pip install -r requirements.txt
```

# Usage

You need an account at [VBN](https://shop.vbn.de/login).

```
python3 vbn-cli.py login <email> <password>
python3 vbn-cli.py sync
```

After tickets have been synchronized, you can export them:

```
python3 vbn-cli.py export
```

**Public Infrastructure, Public Code**

This program can download your mobile tickets from VBN without using the proprietary Fahrplaner App.

# Installation

*(Recommended)* Create a virtual environment using `venv`:
```sh
$ python3 -m venv .venv
$ source .venv/bin/activate
```

Install dependencies:
```sh
$ pip install -r requirements.txt
```

# Usage

You need an account at [VBN](https://shop.vbn.de/login).

```sh
$ python3 vbn-cli.py login <email> <password>
$ python3 vbn-cli.py sync
```

After tickets have been synchronized, you can export them:

```sh
$ python3 vbn-cli export
```

# -*- coding: utf-8 -*-
from setuptools import setup

packages = [
    "quotexpy",
    "quotexpy.exceptions",
    "quotexpy.http",
    "quotexpy.utils",
    "quotexpy.ws",
    "quotexpy.ws.channels",
    "quotexpy.ws.objects",
]

package_data = {"": ["*"]}

install_requires = [
    "appdirs>=1.4.4,<2.0.0",
    "beautifulsoup4>=4.11.2,<5.0.0",
    "certifi>=2022.12.7,<2023.0.0",
    "charset-normalizer>=3.2.0,<4.0.0",
    "cloudscraper>=1.2.71,<2.0.0",
    "idna>=3.4,<4.0",
    "importlib-metadata>=6.2.0,<7.0.0",
    "playwright>=1.39.0,<2.0.0",
    "pyparsing>=3.1.1,<4.0.0",
    "requests-toolbelt>=1.0.0,<2.0.0",
    "requests>=2.31.0,<3.0.0",
    "shutup>=0.2.0,<0.3.0",
    "simplejson>=3.18.3,<4.0.0",
    "soupsieve>=2.4,<3.0",
    "tqdm>=4.65.0,<5.0.0",
    "typing_extensions>=4.5.0,<5.0.0",
    "urllib3>=2.0.5,<3.0.0",
    "websocket-client>=1.6.3,<2.0.0",
    "websockets>=11.0.3,<12.0.0",
    "zipp>=3.17.0,<4.0.0",
]

setup_kwargs = {
    "name": "quotexpy",
    "version": "1.0.39",
    "description": "📈 QuotexPy is a library for interact with qxbroker easily.",
    "long_description": '<div align="center">\n<img src="https://static.scarf.sh/a.png?x-pxid=cf317fe7-2188-4721-bc01-124bb5d5dbb2" />\n\n## <img src="https://github.com/SantiiRepair/quotexpy/blob/main/.github/images/quotex-logo.png?raw=true" height="56"/>\n\n\n**📈 QuotexPy is a library for interact with qxbroker easily.**\n\n______________________________________________________________________\n\n[![License](https://img.shields.io/badge/License-GPL--3.0-magenta.svg)](https://www.gnu.org/licenses/gpl-3.0.txt)\n[![PyPI version](https://badge.fury.io/py/quotexpy.svg)](https://badge.fury.io/py/quotexpy)\n![GithubActions](https://github.com/SantiiRepair/quotexpy/actions/workflows/pylint.yml/badge.svg)\n\n</div>\n\n______________________________________________________________________\n\n## Installing\n\n📈 QuotexPy is tested on Ubuntu 18.04 and Windows 10 with **Python >= 3.10, <= 3.11.**\n```bash\npip install quotexpy\n```\n\nIf you plan to code and make changes, clone and install it locally.\n\n```bash\ngit clone https://github.com/SantiiRepair/quotexpy.git\npip install -e .\n```\n\n### Import\n```python\nfrom quotexpy.new import Quotex\n```\n\n### Examples\nFor examples check out [some](https://github.com/SantiiRepair/quotexpy/blob/main/example/main.py) found in the `example` directory.\n\n### Donations\nIf you feel like showing your love and/or appreciation for this project, then how about shouting me a coffee, beer or something more interesting ;)\n\n<a href="https://www.buymeacoffee.com/SantiiRepair"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a whore&emoji=👯\u200d♀️&slug=SantiiRepair&button_colour=980028&font_colour=ffffff&font_family=Poppins&outline_colour=ffffff&coffee_colour=FFDD00" /></a>\n\n### ⚠️ Atention \nBecause cloudfare blocks requests you should enable `browser=True` to avoid `HTTP 403` errors.\n',
    "author": "Santiago Ramirez",
    "author_email": "santiirepair@gmail.com",
    "maintainer": "None",
    "maintainer_email": "None",
    "url": "https://github.com/SantiiRepair/quotexpy",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "python_requires": ">=3.10,<3.13",
}


setup(**setup_kwargs)

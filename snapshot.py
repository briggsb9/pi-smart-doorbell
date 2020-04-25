#!/usr/bin/env python3

import requests

# take snapshot
response = requests.get('http://localhost:8080/0/action/snapshot')

import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from colorama import Fore, Style, init

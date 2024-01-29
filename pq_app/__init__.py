import json
import random
from flask import Flask, request, render_template, redirect, url_for, flash

from .model import *
from .userCharacter import *
from .gameforms import *
from .pqMonsters import *
from .gameTile import *
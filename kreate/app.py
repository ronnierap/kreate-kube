import jinja2
import shutil
import os

from .environment import Environment


class App:
    def __init__(self, name: str, env: Environment):
        self.name = name
        self.labels = dict()
        self.target_dir = "./target"
        self.env = env

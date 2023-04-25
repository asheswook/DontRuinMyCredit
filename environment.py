import os

class Environment:
    def __init__(self):
        self.dotenv_path = os.path.join(os.getcwd(), '.env')
        self.dotenv_dict = {}
        self.load_dotenv()

    def load_dotenv(self):
        with open(self.dotenv_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                k, v = line.split('=', 1)
                self.dotenv_dict[k] = v
        return self.dotenv_dict

    def get(self, key: str) -> str:
        return self.dotenv_dict[key]

from ptbutil.iteration import dicta

class Config(dicta):
    def from_file(self, conf):
        """Zmienne zaciągnięte z pliku conf muszą być uppercase żeby zostać dodanym do Config"""
        for k, v in conf.__dict__.items():
            if k.isupper():
                self.update({k: v})
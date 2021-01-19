from abc import ABC, ABCMeta, abstractmethod
# from interface import implements, Interface

class ScraperAdapter(ABC):

    # @classmethod
    # def version(self): return "1.0"

    def __init__(self):
      raise NotImplementedError('The class cannot be instantiated')

    @abstractmethod
    def scrape(self) -> dict:
        # raise NotImplementedError("Must override abscract method 'scrape'!")
        pass

    @abstractmethod
    def scrape_day(self) -> dict:
        pass

    @abstractmethod
    def frequency(self) -> str:
        pass

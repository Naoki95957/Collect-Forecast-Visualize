# from abc import ABCMeta, abstractmethod
# from interface import implements, Interface

class ScraperAdapter():
    # __metaclass__ = ABCMeta

    # @classmethod
    # def version(self): return "1.0"

    # @abstractmethod
    # def scrape(self): raise NotImplementedError

    def scrape(self) -> dict:
        pass

    def scrape_day(self) -> dict:
        pass

    def frequency(self) -> str:
        pass

import pandas as pd

class DataHandler:
    def __init__(self, data: pd.DataFrame, interval: str = "1d"):
        self.data = data
        self.interval = interval


    def get_data(self) -> pd.DataFrame:
        return self.data.copy()


    def get_interval(self) -> str:
        return self.interval

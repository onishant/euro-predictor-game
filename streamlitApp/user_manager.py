import pandas as pd
import hashlib
from datetime import datetime

class UserManager:
    def __init__(self, users_file_path=r"H:\EuroPredictorGame\eventData\users.xlsx", fixtures_file_path=r"H:\EuroPredictorGame\eventData\fixture list.xlsx"):
        self.users_file_path = users_file_path
        self.fixtures_file_path = fixtures_file_path

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def get_users(self):
        try:
            df = pd.read_excel(self.users_file_path)
            return df.set_index('username').T.to_dict()
        except FileNotFoundError:
            return {}

    def add_user(self, username, email, password):
        users = self.get_users()
        if username in users:
            raise ValueError("Username already exists")
        
        password_hash = self.hash_password(password)
        new_user = pd.DataFrame([[username, email, password_hash]], columns=["username", "email", "password_hash"])
        
        try:
            df = pd.read_excel(self.users_file_path)
            df = pd.concat([df, new_user], ignore_index=True)
        except FileNotFoundError:
            df = new_user

        df.to_excel(self.users_file_path, index=False)

    def authenticate_user(self, username, password):
        users = self.get_users()
        password_hash = self.hash_password(password)
        return username in users and users[username]["password_hash"] == password_hash

    def save_user_prediction(self, username, match, prediction):
        try:
            df = pd.read_excel(self.users_file_path)
        except FileNotFoundError:
            return
        
        if match not in df.columns:
            df[match] = ""
        
        df.loc[df["username"] == username, match] = prediction
        df.to_excel(self.users_file_path, index=False)

    def get_user_predictions(self):
        try:
            df = pd.read_excel(self.users_file_path)
            return df.set_index('username').T.to_dict('dict')
        except FileNotFoundError:
            return {}

    def get_fixtures_and_results(self):
        try:
            df = pd.read_excel(self.fixtures_file_path)
            # df['Date'] = pd.to_datetime(df['Date'])
            df['Time'] = df['Time'].astype(str)
            df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
            # df['Time'] = pd.to_datetime(df['Time'])
            fixtures = []
            for _, row in df.iterrows():
                team1 = row['Home']
                team2 = row['Away']
                day = row['Day']
                datetime = row['Datetime']
                result = row.get('Result', "")
                fixtures.append((team1, team2, day, datetime, result))
            return fixtures
        except FileNotFoundError:
            return []

    def get_match_start_time(self, match):
        fixtures = self.get_fixtures_and_results()
        for team1, team2, day, datetime, _ in fixtures:
            if f"{team1} vs {team2}" == match:
                return datetime
        return None

    def save_match_result(self, match, result):
        try:
            df = pd.read_excel(self.fixtures_file_path)
            for idx, row in df.iterrows():
                team1 = row['Home']
                team2 = row['Away']
                if f"{team1} vs {team2}" == match:
                    df.at[idx, 'Result'] = result
                    break
            df.to_excel(self.fixtures_file_path, index=False)
        except FileNotFoundError:
            pass

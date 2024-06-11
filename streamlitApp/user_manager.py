import pandas as pd
import hashlib
from datetime import datetime
import streamlit as st
import ast

class UserManager:
    def __init__(self, users_file_path="./eventData/users.xlsx", fixtures_file_path="./eventData/fixture list.xlsx"):
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

    def save_user_prediction(self, username, match, result, score1, score2):
        try:
            df = pd.read_excel(self.users_file_path)
        except FileNotFoundError:
            df = pd.DataFrame(columns=["username", "email", "password_hash"])
        
        if username not in df['username'].values:
            st.warning("User not found.")
            return
        
         # Create the prediction tuple
        prediction_array = [result, int(score1), int(score2)]

        # Add the prediction to the DataFrame
        user_idx = df[df['username'] == username].index[0]
        df.at[user_idx, match] = str(prediction_array)  # Save as string

        # Save the updated DataFrame back to the Excel file
        df.to_excel(self.users_file_path, index=False)

    def get_user_predictions(self):
        
        try:
            df = pd.read_excel(self.users_file_path)
        except FileNotFoundError:
            return {}

        user_predictions = {}
        for _, row in df.iterrows():
            username = row['username']
            user_predictions[username] = {}
            for col in df.columns:
                if col not in ['username', 'email', 'password_hash']:
                    try:
                        prediction = ast.literal_eval(row[col])  # Convert string back to array
                        result, score1, score2 = prediction
                        user_predictions[username][col] = {'result': result, 'score1': score1, 'score2': score2}
                    except (SyntaxError, ValueError, TypeError):
                        continue

        return user_predictions

    def get_fixtures_and_results(self):
        try:
            df = pd.read_excel(self.fixtures_file_path)
            df['Time'] = df['Time'].astype(str)
            df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
            fixtures = []
            for _, row in df.iterrows():
                team1 = row['Home']
                team2 = row['Away']
                day = row['Day']
                datetime = row['Datetime']
                result_score1 = row.get('Home_Score', '')
                result_score2 = row.get('Away_Score', '')
                fixtures.append((team1, team2, day, datetime, result_score1, result_score2))
            return fixtures
        except FileNotFoundError:
            return []

    def get_match_start_time(self, match):
        fixtures = self.get_fixtures_and_results()
        for team1, team2, day, datetime, _1, _2 in fixtures:
            if f"{team1} vs {team2}" == match:
                return datetime
        return None

    def save_match_result(self, match, score1, score2):
        try:
            df = pd.read_excel(self.fixtures_file_path)
            for idx, row in df.iterrows():
                team1 = row['Home']
                team2 = row['Away']

                if f"{team1} vs {team2}" == match:
                    df.at[idx, 'Home_Score'] = int(score1)
                    df.at[idx, 'Away_Score'] = int(score2)
                    break
            df.to_excel(self.fixtures_file_path, index=False)
        except FileNotFoundError:
            pass

    def update_leaderboard(self):
        try:
            users_df = pd.read_excel(self.users_file_path)
            fixtures_df = pd.read_excel(self.fixtures_file_path)
        except FileNotFoundError:
            return

        leaderboard = {}
        for _, user_row in users_df.iterrows():
            username = user_row['username']
            user_points = 0
            for fixture_idx, fixture_row in fixtures_df.iterrows():
                team1 = fixture_row['Home']
                team2 = fixture_row['Away']
                match = f"{team1} vs {team2}"
                if match not in user_row:
                    continue

                try:
                    prediction = ast.literal_eval(user_row[match])
                    result, predicted_score1, predicted_score2 = prediction
                    actual_score1 = fixture_row.get('Home_Score')
                    actual_score2 = fixture_row.get('Away_Score')

                    if pd.isna(actual_score1) or pd.isna(actual_score2):
                        continue

                    # Award points for correct match result prediction
                    if (result == team1 and actual_score1 > actual_score2) or \
                    (result == team2 and actual_score2 > actual_score1) or \
                    (result == "Draw" and actual_score1 == actual_score2):
                        user_points += 10

                    # Award points for correct score predictions
                    if predicted_score1 == actual_score1:
                        user_points += 5
                    if predicted_score2 == actual_score2:
                        user_points += 5
                except (SyntaxError, ValueError, TypeError):
                    continue

            leaderboard[username] = int(user_points)

        # Save the leaderboard to session state or any other method of persistence
        self.leaderboard = leaderboard


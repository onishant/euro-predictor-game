import streamlit as st
import pandas as pd
from datetime import datetime

class DisplayManager:
    def __init__(self, user_manager):
        self.user_manager = user_manager

    def user_predictions_page(self, fixtures):
        st.subheader("Enter Your Predictions")
        username = st.session_state["username"]
        now = datetime.now()

        # Retrieve existing predictions for the current user
        user_predictions = self.user_manager.get_user_predictions().get(username, {})

        # Group fixtures by date
        fixtures_by_date = {}
        for team1, team2, day, date, result in fixtures:
            if date not in fixtures_by_date:
                fixtures_by_date[date] = []
            fixtures_by_date[date].append((team1, team2))

        for date, matches in fixtures_by_date.items():
            st.markdown(f"### Matches on {day} {date.strftime('%d %b')}")
            for team1, team2 in matches:
                match = f"{team1} vs {team2}"
                match_start_time = self.user_manager.get_match_start_time(match)
                print(match_start_time)
                saved_prediction = user_predictions.get(match, "")

                if match_start_time and now >= match_start_time:
                    st.text(f"Match {match} has already started. Prediction locked: {saved_prediction}")
                    continue

                prediction = st.selectbox(
                    f"{team1} vs {team2}",
                    (team1, team2, "Draw"),
                    index=(0 if saved_prediction == team1 else (1 if saved_prediction == team2 else 2)),
                    key=f"{team1}_vs_{team2}_pred"
                )

                if st.button(f"Submit Prediction for {team1} vs {team2}"):
                    self.user_manager.save_user_prediction(username, match, prediction)
                    st.success(f"Prediction for {team1} vs {team2} submitted: {prediction}")

    def submit_results_page(self, fixtures):
        st.subheader("Submit Match Results")
        for team1, team2, day, date, _ in fixtures:
            match = f"{team1} vs {team2}"
            result = st.selectbox(f"Match Result: {match}", (team1, team2, "Draw"), key=f"result_{match}")
            if st.button(f"Submit Result for {match}"):
                st.session_state["results"][match] = result
                self.user_manager.save_match_result(match, result)
                st.success(f"Result for {match} submitted")

    def display_leaderboard(self):
        st.subheader("Leaderboard")

        # Read user predictions and results from Excel sheets
        user_predictions = self.user_manager.get_user_predictions()
        fixtures_and_results = self.user_manager.get_fixtures_and_results()

        leaderboard = {}
        for team1, team2, day, date, result in fixtures_and_results:
            match = f"{team1} vs {team2}"
            if result:
                for username, predictions in user_predictions.items():
                    if match in predictions and predictions[match] == result:
                        if username in leaderboard:
                            leaderboard[username] += 1
                        else:
                            leaderboard[username] = 1

        # Convert leaderboard to a DataFrame and display
        leaderboard_df = pd.DataFrame(list(leaderboard.items()), columns=["Username", "Points"])
        leaderboard_df = leaderboard_df.sort_values(by="Points", ascending=False)
        st.table(leaderboard_df)

    def display_fixtures_and_results(self):
        st.subheader("Fixtures and Results")
        fixtures = self.user_manager.get_fixtures_and_results()
        data = [{"Match": f"{team1} vs {team2}", "Result": result if result else "Pending"} for team1, team2, day, date, result in fixtures]
        df = pd.DataFrame(data)
        st.table(df)

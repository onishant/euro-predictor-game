import streamlit as st
import pandas as pd
from datetime import datetime
import io

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
        for team1, team2, day, date, result_score1, result_score2 in fixtures:
            if date not in fixtures_by_date:
                fixtures_by_date[date] = []
            fixtures_by_date[date].append((team1, team2))

        for date, matches in fixtures_by_date.items():
            st.markdown(f"### Matches on {day} {date.strftime('%d %b')}")
            for team1, team2 in matches:
                match = f"{team1} vs {team2}"
                match_start_time = self.user_manager.get_match_start_time(match)

                saved_prediction = user_predictions.get(match, {})

                if match_start_time and now >= match_start_time:
                    st.text(f"Match {match} has already started. Prediction locked: {saved_prediction}")
                    continue

                col1, col2, col3 = st.columns(3)
                with col1:
                    result = st.selectbox(f"Result for {team1} vs {team2}", [team1, team2, "Draw"], key=f"{team1}_{team2}_result", index=["Draw", team1, team2].index(saved_prediction.get('result', "Draw")))
                with col2:
                    score1 = st.number_input(f"{team1} score", min_value=0, value=saved_prediction.get('score1', 0), key=f"{team1}_{team2}_score1")
                with col3:
                    score2 = st.number_input(f"{team2} score", min_value=0, value=saved_prediction.get('score2', 0), key=f"{team1}_{team2}_score2")

                if st.button(f"Submit Prediction for {team1} vs {team2}"):
                    score1 = int(score1)  # Ensure score1 is an integer
                    score2 = int(score2)  # Ensure score2 is an integer

                    if (result == team1 and score1 <= score2) or (result == team2 and score2 <= score1) or (result == "Draw" and score1 != score2):
                        st.warning("Inconsistent prediction: the winner must have more goals than the loser, and a draw must have equal scores.")
                    else:
                        self.user_manager.save_user_prediction(username, match, result, score1, score2)
                        st.success(f"Prediction for {team1} vs {team2} submitted: {result} {team1} {score1} - {score2} {team2}")

    def submit_results_page(self, fixtures):
        st.subheader("Submit Match Results")
        for team1, team2, day, date, _1, _2 in fixtures:
            match = f"{team1} vs {team2}"
            col1, col2, col3 = st.columns(3)
            with col1:
                score1 = st.number_input(f"{team1} score", min_value=0, key=f"{team1}_{team2}_result_score1")
            with col2:
                score2 = st.number_input(f"{team2} score", min_value=0, key=f"{team1}_{team2}_result_score2")
            with col3:
                if st.button(f"Submit Result for {team1} vs {team2}"):
                    score1 = int(score1)  # Ensure score1 is an integer
                    score2 = int(score2)  # Ensure score2 is an integer
                    self.user_manager.save_match_result(match, score1, score2)
                    st.success(f"Result for {team1} vs {team2} submitted: {team1} {score1} - {score2} {team2}")

    def display_leaderboard(self):
        st.subheader("Leaderboard")
        self.user_manager.update_leaderboard()
        leaderboard = self.user_manager.leaderboard

        leaderboard_data = [{"Username": username, "Points": int(points)} for username, points in leaderboard.items()]
        leaderboard_df = pd.DataFrame(leaderboard_data)
        leaderboard_df = leaderboard_df.sort_values(by="Points", ascending=False)
        st.table(leaderboard_df)

    def display_fixtures_and_results(self):
        st.subheader("Fixtures and Results")
        try:
            fixtures_df = pd.read_excel(self.user_manager.fixtures_file_path)
        except FileNotFoundError:
            st.warning("Fixtures file not found.")
            return

        def format_score(score):
            return "NA" if pd.isna(score) else int(score)

        fixtures_df['Home_Score'] = fixtures_df['Home_Score'].apply(format_score)
        fixtures_df['Away_Score'] = fixtures_df['Away_Score'].apply(format_score)

        st.table(fixtures_df[['Date', 'Home', 'Home_Score', 'Away', 'Away_Score']])

    def export_files(self):
        st.subheader("Export Data Files")

        def convert_df_to_excel(df):
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='openpyxl')
            df.to_excel(writer, index=False)
            writer.close()
            processed_data = output.getvalue()
            return processed_data

        # Export users file
        users_df = pd.read_excel(self.user_manager.users_file_path)
        st.download_button(
            label="Export Users Data",
            data=convert_df_to_excel(users_df),
            file_name='users.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # Export fixtures file
        fixtures_df = pd.read_excel(self.user_manager.fixtures_file_path)
        st.download_button(
            label="Export Fixtures Data",
            data=convert_df_to_excel(fixtures_df),
            file_name='fixture list.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

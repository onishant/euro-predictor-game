import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import pytz

class DisplayManager:
    def __init__(self, user_manager):
        self.user_manager = user_manager

    def user_predictions_page(self, fixtures):
        st.subheader("Enter Your Predictions")
        username = st.session_state["username"]
        now = datetime.now()
        # print("now", now)
        now_germany = now + timedelta(hours=2)
        # print("German time", now_germany)
        # Retrieve existing predictions for the current user
        user_predictions = self.user_manager.get_user_predictions().get(username, {})

        # Separately display old and upcoming matches
        old_matches_by_date = {}
        upcoming_matches_by_date = {}

        # Separate fixtures into old matches and upcoming matches, grouped by date
        for team1, team2, day, datetime_obj, _1, _2 in fixtures:
            match_date = datetime_obj.date()
            # print(match_date, now.date())
            match = (team1, team2, day, datetime_obj)
            if match_date < now.date():
                if match_date not in old_matches_by_date:
                    old_matches_by_date[match_date] = []
                old_matches_by_date[match_date].append(match)
            else:
                if match_date not in upcoming_matches_by_date:
                    upcoming_matches_by_date[match_date] = []
                upcoming_matches_by_date[match_date].append(match)

        # Display old matches in a dropdown
        if old_matches_by_date:
            with st.expander("Old Matches"):
                for date in sorted(old_matches_by_date.keys()):
                    st.markdown(f"### Matches on {date.strftime('%d %b %Y')}")
                    for team1, team2, day, _ in old_matches_by_date[date]:
                        match = f"{team1} vs {team2}"
                        match_start_time = self.user_manager.get_match_start_time(match)

                        saved_prediction = user_predictions.get(match, {})
                        
                        if match_start_time and now_germany >= match_start_time:
                            st.text(f"Match {match} has already started. Prediction locked: {saved_prediction}")
                        
                            continue
        
        # Display upcoming matches
        if upcoming_matches_by_date:
            st.markdown("### Upcoming Matches")
            for date in sorted(upcoming_matches_by_date.keys()):
                print(upcoming_matches_by_date)
                st.markdown(f"### Matches on {date.strftime('%d %b %Y')}")
                for team1, team2, day, _ in upcoming_matches_by_date[date]:
                    match = f"{team1} vs {team2}"

                    match_start_time = self.user_manager.get_match_start_time(match)

                    saved_prediction = user_predictions.get(match, {})
                    
                    if match_start_time and now_germany >= match_start_time:
                        st.text(f"Match {match} has already started. Prediction locked: {saved_prediction}")
                    
                        continue

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        result = st.selectbox(f"Result for {team1} vs {team2}", [team1, team2, "Draw"], key=f"{team1}_{team2}_result", index=["Draw", team1, team2].index(saved_prediction.get('result', "Draw")))
                    with col2:
                        score1 = st.number_input(f"{team1} score", min_value=0, value=saved_prediction.get('score1', 0), key=f"{team1}_{team2}_score1")
                    with col3:
                        score2 = st.number_input(f"{team2} score", min_value=0, value=saved_prediction.get('score2', 0), key=f"{team1}_{team2}_score2")
                    st.markdown(f"**Current Prediction**: {saved_prediction.get('result', 'N/A')} {saved_prediction.get('score1', 'N/A')} - {saved_prediction.get('score2', 'N/A')}")

                    if st.button(f"Submit Result for {team1} vs {team2}"):
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
        leaderboard_df = leaderboard_df.sort_values(by="Points", ascending=False).reset_index(drop=True)

        # Add ranking column
        leaderboard_df.insert(0, 'Rank', leaderboard_df.index + 1)

        # Highlight the top three positions
        def highlight_top_three(row):
            if row.name == 0:  # First row
                return ['background-color: gold'] * len(row)
            elif row.name == 1:  # Second row
                return ['background-color: silver'] * len(row)
            elif row.name == 2:  # Third row
                return ['background-color: #cd7f32'] * len(row)  # Bronze color
            else:
                return [''] * len(row)

        st.dataframe(leaderboard_df.style.apply(highlight_top_three, axis=1))

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

import streamlit as st
from user_manager import UserManager
from display_manager import DisplayManager

# Initialize UserManager and DisplayManager
user_manager = UserManager()
display_manager = DisplayManager(user_manager)

# Initialize session state
if "users" not in st.session_state:
    st.session_state["users"] = user_manager.get_users()
if "predictions" not in st.session_state:
    st.session_state["predictions"] = []
if "leaderboard" not in st.session_state:
    st.session_state["leaderboard"] = {}
if "results" not in st.session_state:
    st.session_state["results"] = {}

# Page configuration
st.set_page_config(page_title="IN-Euro Predict Game", layout="centered")

# User Authentication
def user_authentication():
    menu = ["Sign Up", "Login"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Sign Up":
        st.subheader("Create a New Account")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type='password')
        if st.button("Sign Up"):
            try:
                user_manager.add_user(username, email, password)
                st.success("You have successfully created an account")
            except ValueError as e:
                st.warning(str(e))
    
    elif choice == "Login":
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Login"):
            if user_manager.authenticate_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Welcome {username}")
                st.experimental_rerun()
            else:
                st.warning("Invalid username or password")

def logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.success("You have been logged out.")
    st.experimental_rerun()

# Main Application
def main():
    st.title("IN-Euro Predict Game")
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        user_authentication()
    else:
        fixtures = display_manager.user_manager.get_fixtures_and_results()
        username = st.session_state["username"]
        if username == "admin":
            menu = ["Submit Results", "Leaderboard", "Fixtures and Results", "Export Data", "Logout"]
        else:
            menu = ["Your Predictions", "Leaderboard", "Fixtures and Results", "Logout"]
        choice = st.sidebar.selectbox("Menu", menu, key="logged_in_menu")
        
        if choice == "Your Predictions":
            display_manager.user_predictions_page(fixtures)
        elif choice == "Submit Results":
            display_manager.submit_results_page(fixtures)
        elif choice == "Leaderboard":
            display_manager.display_leaderboard()
        elif choice == "Fixtures and Results":
            display_manager.display_fixtures_and_results()
        elif choice == "Export Data":
            display_manager.export_files()
        elif choice == "Logout":
            logout()

if __name__ == '__main__':
    main()

# LetterDB

> Check out the [running version of the website](https://obruchevletters.pythonanywhere.com/)

This repository contains the source code for LetterDB, a web application that allows the interactive storage of letters of Vladimir Obruchev.

## Installation
1) Clone the repository to your local machine.
2) Create a virtual environment for the project.
3) Install the required packages using pip install -r requirements.txt.
4) Create a .env file in the root directory of the project. Add the following parameters to the .env file:

    
    `GOOGLE_CLIENT_SECRET=<your_google_client_secret>`
    `GOOGLE_CLIENT_ID=<your_google_client_id>`
    `APPROVED_EMAILS=<comma_separated_list_of_approved_emails>`

    Replace `<your_google_client_secret>` and `<your_google_client_id>` with your Google API credentials. You can obtain these credentials from [the google API dashboard](https://console.cloud.google.com/apis/dashboard).
5) Run the application using python3 app.py. \
Please do note that this will run in debug mode with an unsigned certificate. Proper hosting is required for release.


I hope this helps! Let me know if you have any other questions.
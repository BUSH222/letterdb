# LetterDB

> Check out the [running version of the website](https://obruchevletters.pythonanywhere.com/)

This repository contains the source code for LetterDB, a web application that allows the interactive storage of letters of Vladimir Obruchev.

## Installation
1) Clone the repository to your local machine.
2) Create a virtual environment for the project.
3) Install the required packages using pip install -r requirements.txt.
4) Use the built in `manager` tool to quickly set everything up:
    - open terminal and cd to the directory of the project
    - run `python manager.py quick_setup --secret=<your_google_client_secret> --id=<your_google_client_id> --emails=<space_separated_list_of_approved_emails>`

    Replace `<your_google_client_secret>` and `<your_google_client_id>` with your Google API credentials. You can obtain these credentials from [the google API dashboard](https://console.cloud.google.com/apis/dashboard).

    The list of approved emails should look like this:
    `"example1@domain.com example2@domain.com example3@domain.com"`
5) Run the application using python3 app.py. \
Please do note that this will run with an unsigned certificate. Proper hosting is required for release.

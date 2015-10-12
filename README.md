# Udacity Full Stack Nanodegree Project 3: 
An application that provides a list of items within a variety of categories as well as providing a user registration and authentication system.

## Usage
### Dependencies
*Flask* (tested with version 0.10.1)  
*Sqlalchemy* (tested with version 1.0.8)  
*oauth2client* (tested with version 1.5.1)  
*requests* (tested with version 2.8.0)

### Setup
Rename *"private_example_files"* folder to *"private"* and edit the following files:  

- *secrets.json* (flask app secrets):  
Set "YOUR_APP_KEY" to a private value of your choosing.

- *fb_client_secrets.json* (facebook oauth settings):  
Set "YOUR_APP_ID" and "YOUR_APP_SECRET" to your own values (obtainable [here](https://developers.facebook.com/apps/))

- *google_client_secret.json* (google oauth settings):  
Set "YOUR_CLIENT_ID" and "YOUR_CLIENT_SECRET" to your own values (obtainable [here](https://console.developers.google.com/project))

Run *populate_database.py* to add some sample data taken from [MIT OCW](http://ocw.mit.edu/courses/)


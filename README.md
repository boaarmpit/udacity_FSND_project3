# Udacity Full Stack Nanodegree Project 3: 
*"An application that provides a list of items within a variety of categories as well as providing a user registration and authentication system."*  
This application lists university classes categorized by subject, and enables teachers to log in and add/edit/delete classes.  

###Features  

- Can list all university classes sorted by subject
- Registered users can add classes and edit/delete their own classes  
  (using Facebook and Gmail as Oauth providers)
- Support for addition/editing/deletion of class images
- JSON and XML endpoints
- Anti CSRF tokens


## Usage
### Dependencies
*Flask* (tested with version 0.10.1)  
*Sqlalchemy* (tested with version 1.0.8)  
*oauth2client* (tested with version 1.5.1)  
*requests* (tested with version 2.8.0)

### Setup
1. Rename *"private_example_files"* folder to *"private"* and edit the following files:  

  - *secrets.json* (flask app secrets):  
  Set "YOUR_APP_KEY" to a private value of your choosing.

  - *fb_client_secrets.json* (facebook oauth settings):  
  Set "YOUR_APP_ID" and "YOUR_APP_SECRET" to your own values (obtainable [here](https://developers.facebook.com/apps/))

  - *google_client_secret.json* (google oauth settings):  
  Set "YOUR_CLIENT_ID" and "YOUR_CLIENT_SECRET" to your own values (obtainable [here](https://console.developers.google.com/project))

2. Run *populate_database.py* to add some sample data taken from [MIT OCW](http://ocw.mit.edu/courses/)
3. Run *app.py* to test on http://localhost:5000/
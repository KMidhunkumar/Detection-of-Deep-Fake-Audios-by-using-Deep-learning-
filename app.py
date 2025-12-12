from flask import Flask, url_for, redirect, render_template, request, session
import mysql.connector
import pandas as pd
import joblib
import os
import numpy as np
import tensorflow as tf
import librosa
from tensorflow.keras.models import load_model

def extract_mfcc(file_path, max_pad_len=174):
    try:
        audio, sample_rate = librosa.load(file_path, res_type='kaiser_fast')
        mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=40)
        if mfccs.shape[1] > max_pad_len:
            mfccs = mfccs[:, :max_pad_len]
        else:
            pad_width = max_pad_len - mfccs.shape[1]
            mfccs = np.pad(mfccs, pad_width=((0, 0), (0, pad_width)), mode='constant')
    except Exception as e:
        print(f"Error encountered while parsing file {file_path}: {e}")
        return None
    return mfccs

def predict_audio_class(file_path, model_path='cnn.h5'):
    # Load the model
    model = load_model(model_path)
    
    # Extract features from the audio file
    features = extract_mfcc(file_path)
    if features is None:
        print("Could not extract features from the file")
        return None
    
    # Reshape the features to match the input shape of the model
    features = features[np.newaxis, ..., np.newaxis]
    
    # Predict the class of the audio file
    prediction = model.predict(features)
    predicted_class = np.argmax(prediction, axis=1)
    
    # Translate the predicted class index into a meaningful label
    class_labels = ['Real', 'Fake']  # Adjust according to your classes
    predicted_label = class_labels[predicted_class[0]]
    
    return predicted_label

app = Flask(__name__)
app.secret_key = 'admin'

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3306",
    database='deep_fake'
)

mycursor = mydb.cursor()

def executionquery(query,values):
    mycursor.execute(query,values)
    mydb.commit()
    return

def retrivequery1(query,values):
    mycursor.execute(query,values)
    data = mycursor.fetchall()
    return data

def retrivequery2(query):
    mycursor.execute(query)
    data = mycursor.fetchall()
    return data



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']
        if password == c_password:
            query = "SELECT UPPER(email) FROM users"
            email_data = retrivequery2(query)
            email_data_list = []
            for i in email_data:
                email_data_list.append(i[0])
            if email.upper() not in email_data_list:
                query = "INSERT INTO users (email, password) VALUES (%s, %s)"
                values = (email, password)
                executionquery(query, values)
                return render_template('login.html', message="Successfully Registered!")
            return render_template('register.html', message="This email ID is already exists!")
        return render_template('register.html', message="Conform password is not match!")
    return render_template('register.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        query = "SELECT UPPER(email) FROM users"
        email_data = retrivequery2(query)
        email_data_list = []
        for i in email_data:
            email_data_list.append(i[0])

        if email.upper() in email_data_list:
            query = "SELECT UPPER(password) FROM users WHERE email = %s"
            values = (email,)
            password__data = retrivequery1(query, values)
            if password.upper() == password__data[0][0]:
                global user_email
                user_email = email

                return render_template('home.html')
            return render_template('login.html', message= "Invalid Password!!")
        return render_template('login.html', message= "This email ID does not exist!")
    return render_template('login.html')


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/upload', methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        myfile = request.files['file']
        fn = myfile.filename
        accepted_formats = ['mp3', 'wav', 'ogg', 'flac']
        if fn.split('.')[-1].lower() not in accepted_formats:
            message = "Invalid file format. Accepted formats: {}".format(', '.join(accepted_formats))
            return render_template("audio.html", message = message)
        mypath = os.path.join('static/audio/', fn)
        myfile.save(mypath)
        predicted_class = predict_audio_class(mypath)
        print(f"Predicted class: {predicted_class}")
        return render_template('upload.html',result=predicted_class)
    return render_template('upload.html')



if __name__ == '__main__':
    app.run(debug = True)
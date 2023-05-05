# HitMatch - the song recommender project

![logo](https://raw.githubusercontent.com/ralphmartynward/ironhack_06_song-recommender/master/hitmatch.png)

Music Recommendation System: Web Scraping, Database, Clustering, and Machine Learning

## Overview

This project demonstrates the process of building a music recommendation system using web scraping, database management, clustering techniques, and machine learning. We start by scraping hot songs from the web, checking a database of existing songs, and allowing the user to input a song. Then, we fetch song features from the Spotify API and utilize clustering methods such as KMeans and DBSCAN to provide song recommendations. Finally, we leverage a machine learning model to find the most suitable cluster for the input song and recommend similar songs based on the identified cluster. 

You can view the notebook of the progress under the `notebooks` folder. 
You can view the presentation of the project under the `presentation` folder.

### Project Structure

1. **Web Scraping**: Scrape a list of hot songs from a reliable online source https://www.billboard.com/charts/hot-100/. This data will be used as a starting point for the recommendation system.

2. **Database Management**: Check a pre-existing database of songs to know what songs we can recommend to the user.

3. **Spotify API**: Fetch the user input song's features using the Spotify API. These features will be used to determine the most suitable cluster for the song.

4. **Data Preprocessing**: Preprocess the song features using a scaler to ensure that all features have the same weight when clustering.

5. **Clustering**: Utilize clustering methods such as KMeans and DBSCAN to group similar songs together based on their features. Train a machine learning model on the existing database of songs and their features.
Kmeans gave the best results in our case
![cluster](https://raw.githubusercontent.com/ralphmartynward/ironhack_06_song-recommender/master/clusters.png)


6. **Recommendation**: Once the user input song's features are processed and the model identifies the most suitable cluster, recommend similar songs to the user based on the songs present in the identified cluster.

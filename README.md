#  Movie Recommendation System

##  Overview
This project is a **content-based movie recommendation system**. It helps users discover movies based on their preferences by analyzing movie attributes such as **genre, IMDb score, and other metadata**.

The system processes a large movie dataset, performs data preprocessing and analysis, and generates personalized recommendations using machine learning techniques. A web-based interface was also developed to allow users to search and receive recommendations.

---

##  Features
- Content-based movie recommendations  
- Genre transformation using one-hot encoding  
- Clustering of similar movies using K-Means  
- Ranking recommendations using cosine similarity  
- Data preprocessing (handling missing values, encoding, scaling)  
- MongoDB-based data storage design  
- Web-based interface using Flask *(not included in this repository)*  

---

##  Technologies Used
- Python  
- Pandas, NumPy  
- Scikit-learn  
- MongoDB Atlas  
- Flask (Backend)  
- HTML, CSS (Frontend)  
- Google Colab  

---

##  Dataset
- IMDb 5000 Movie Dataset  
- ~5000 movies with 26 features  
- Includes:
  - IMDb score  
  - Genres  
  - Budget  
  - Reviews  
  - Cast and crew information  

The dataset was cleaned and preprocessed before applying recommendation techniques.

---

##  Methodology

### Data Preprocessing
- Handled missing values using:
  - Median imputation for numerical data  
  - "Unknown" values for categorical data  
- Standardized numerical features  
- Encoded categorical variables (ordinal and nominal encoding)  

### Genre Transformation
- Converted genre strings into lists  
- Applied MultiLabelBinarizer for one-hot encoding  

### Recommendation Algorithm
- K-Means clustering used to group similar movies  
- Cosine similarity used to rank movies within clusters  
- Recommendations based mainly on:
  - Genre similarity  
  - IMDb score  

### Database Design
- Designed using MongoDB (NoSQL)  
- Used embedded document model for faster data retrieval  
- Indexed key fields for improved query performance  

---

##  Live Demo
https://flask-movie-app-khwp.onrender.com/login  

---


##  Future Improvements 
- Improve recommendation accuracy using additional features  
- Integrate newer movie datasets (post-2016)  
- Explore hybrid recommendation systems  

---


##  References
- IMDb 5000 Movie Dataset (Kaggle)  
- Scikit-learn Documentation  
- MongoDB Documentation  

import pickle
import streamlit as st
import requests
import os

OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# -----------------------------
# LOAD DATA (CACHE SAFE)
# -----------------------------
@st.cache_resource
def load_movies():
    return pickle.load(open("movies.pkl", "rb"))


@st.cache_resource
def load_similarity():
    url = "https://www.dropbox.com/scl/fi/qi7tanbwec7fiz46qce1q/similarity.pkl?rlkey=ayt7qfng0z3i4bxn18u7iwa57&st=05n7ullf&dl=1"
    
    response = requests.get(url, timeout=30)
    
    # Save once
    with open("similarity.pkl", "wb") as f:
        f.write(response.content)

    return pickle.load(open("similarity.pkl", "rb"))


movies = load_movies()
similarity = load_similarity()


# -----------------------------
# POSTER FETCH FUNCTION
# -----------------------------
TITLE_MAP = {
    "Harry Potter and the Philosopher's Stone": 
    "Harry Potter and the Sorcerer's Stone",
}


def fetch_poster(movie_title):
    try:
        clean_title = movie_title.strip()
        search_title = TITLE_MAP.get(clean_title, clean_title)

        encoded = requests.utils.quote(search_title)
        url = f"http://www.omdbapi.com/?t={encoded}&apikey={OMDB_API_KEY}&type=movie"
        
        data = requests.get(url, timeout=5).json()

        if data.get('Response') == 'True':
            poster = data.get('Poster')
            if poster and poster != "N/A":
                return poster

        # fallback Wikipedia
        wiki_title = requests.utils.quote(clean_title.replace(" ", "_"))
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
        
        wiki_data = requests.get(wiki_url, timeout=5).json()
        thumb = wiki_data.get("thumbnail", {}).get("source", "")
        
        if thumb:
            return thumb

        return f"https://via.placeholder.com/300x450.png?text={clean_title}"

    except:
        return "https://via.placeholder.com/300x450.png?text=Error"


# -----------------------------
# RECOMMENDATION FUNCTION
# -----------------------------
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]

    distances = list(enumerate(similarity[index]))
    distances = sorted(distances, key=lambda x: x[1], reverse=True)

    recommended_names = []
    recommended_posters = []

    for i in distances[1:6]:
        name = movies.iloc[i[0]].title
        recommended_names.append(name)
        recommended_posters.append(fetch_poster(name))

    return recommended_names, recommended_posters


# -----------------------------
# UI
# -----------------------------
st.header("🎬 Movie Recommendation System")

movie_list = movies['title'].values

selected_movie = st.selectbox(
    "Type or select a movie",
    movie_list
)

if st.button("Show Recommendation"):
    with st.spinner("Fetching recommendations..."):
        names, posters = recommend(selected_movie)

    cols = st.columns(5)

    for col, name, poster in zip(cols, names, posters):
        with col:
            st.image(poster, use_container_width=True)
            st.markdown(
                f"<p style='text-align:center; font-size:13px; font-weight:bold;'>{name}</p>",
                unsafe_allow_html=True
            )
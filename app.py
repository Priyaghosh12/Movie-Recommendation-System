import pickle
import streamlit as st
import requests
import os

OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# OMDB uses American titles — map UK/international titles to US titles
TITLE_MAP = {
    "Harry Potter and the Philosopher's Stone": "Harry Potter and the Sorcerer's Stone",
}

def fetch_poster(movie_title):
    try:
        clean_title = movie_title.strip()

        # Check if title needs to be mapped to US version
        search_title = TITLE_MAP.get(clean_title, clean_title)

        # 1st — Try OMDB with mapped title
        encoded = requests.utils.quote(search_title)
        url = f"http://www.omdbapi.com/?t={encoded}&apikey={OMDB_API_KEY}&type=movie"
        response = requests.get(url, timeout=5)
        data = response.json()
        print(f"OMDB [{search_title}]: {data.get('Response')} | {data.get('Poster')}")
        if data.get('Response') == 'True':
            poster = data.get('Poster', '')
            if poster and poster != 'N/A':
                return poster

        # 2nd — Try without apostrophes/special chars
        simplified = clean_title.replace("'", "").replace(":", "").replace("-", " ")
        encoded2 = requests.utils.quote(simplified)
        url2 = f"http://www.omdbapi.com/?t={encoded2}&apikey={OMDB_API_KEY}&type=movie"
        response2 = requests.get(url2, timeout=5)
        data2 = response2.json()
        if data2.get('Response') == 'True':
            poster2 = data2.get('Poster', '')
            if poster2 and poster2 != 'N/A':
                return poster2

        # 3rd — Wikipedia fallback
        wiki_title = requests.utils.quote(clean_title.replace(' ', '_'))
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}_film"
        wiki_response = requests.get(wiki_url, timeout=5)
        wiki_data = wiki_response.json()
        thumbnail = wiki_data.get('thumbnail', {}).get('source', '')
        if thumbnail:
            return thumbnail

        # 4th — Wikipedia without _film
        wiki_url2 = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
        wiki_response2 = requests.get(wiki_url2, timeout=5)
        wiki_data2 = wiki_response2.json()
        thumbnail2 = wiki_data2.get('thumbnail', {}).get('source', '')
        if thumbnail2:
            return thumbnail2

        # 5th — Placeholder
        return f"https://via.placeholder.com/300x450.png?text={requests.utils.quote(clean_title)}"

    except Exception as e:
        print(f"Error for {movie_title}: {e}")
        return "https://via.placeholder.com/300x450.png?text=Error"


def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(
        list(enumerate(similarity[index])),
        reverse=True,
        key=lambda x: x[1]
    )
    recommended_movie_names = []
    recommended_movie_posters = []

    for i in distances[1:6]:
        name = movies.iloc[i[0]].title
        recommended_movie_names.append(name)
        recommended_movie_posters.append(fetch_poster(name))

    return recommended_movie_names, recommended_movie_posters


st.header('🎬 Movie Recommendation System')

movies = pickle.load(open('movies.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button('Show Recommendation'):
    with st.spinner('Fetching recommendations...'):
        names, posters = recommend(selected_movie)

    cols = st.columns(5)
    for col, name, poster in zip(cols, names, posters):
        with col:
            st.image(poster, width='stretch')
            st.markdown(
                f"<p style='text-align:center; font-size:13px; font-weight:bold; color:white;'>{name}</p>",
                unsafe_allow_html=True
            )
import pandas as pd

# Load the original MovieLens data
ratings = pd.read_csv(
    "ml-100k/u.data", sep="\t", names=["userId", "movieId", "rating", "timestamp"]
)
movies = pd.read_csv(
    "ml-100k/u.item",
    sep="|",
    encoding="ISO-8859-1",
    names=["movieId", "title", "release_date", "video_release_date", "IMDb_URL"]
    + [
        "unknown",
        "Action",
        "Adventure",
        "Animation",
        "Children's",
        "Comedy",
        "Crime",
        "Documentary",
        "Drama",
        "Fantasy",
        "Film-Noir",
        "Horror",
        "Musical",
        "Mystery",
        "Romance",
        "Sci-Fi",
        "Thriller",
        "War",
        "Western",
    ],
)

# Convert the genre columns to a single "genres" column
genre_columns = movies.columns[5:]  # all genre flags


def get_genres(row):
    return "|".join([genre for genre in genre_columns if row[genre] == 1])


movies["genres"] = movies.apply(get_genres, axis=1)
movies = movies[["movieId", "title", "genres"]]  # Keep only relevant columns

users = pd.read_csv(
    "ml-100k/u.user", sep="|", names=["userId", "age", "gender", "occupation", "zip"]
)
users = users[["userId", "age", "gender"]]

# Save as CSVs in the correct location
ratings.to_csv("data/movielens/ratings.csv", index=False)
movies.to_csv("data/movielens/movies.csv", index=False)
users.to_csv("data/movielens/users.csv", index=False)

print("✅ CSV files created in data/movielens/ with genres column")

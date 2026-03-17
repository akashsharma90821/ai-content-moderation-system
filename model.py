import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from langdetect import detect

# Load dataset
df = pd.read_csv("data/toxicity.csv")  # Your dataset

X = df['text']
y = df['is_toxic']

# English model
vectorizer = TfidfVectorizer(stop_words='english')
X_vec = vectorizer.fit_transform(X)
model = LogisticRegression()
model.fit(X_vec, y)

# Keywords for categories (English + simple Korean)
category_keywords = {
    'Hate': ['racist','jew','muslim','hater','혐오','차별'],
    'Insult': ['stupid','idiot','dumb','moron','바보','멍청이'],
    'Threat': ['kill','hurt','attack','destroy','죽여','위협'],
    'Sexual': ['sex','porn','nude','섹스','포르노'],
    'Spam': ['buy now','subscribe','click','free','무료','클릭']
}

def get_category(comment):
    comment_lower = comment.lower()
    for cat, keywords in category_keywords.items():
        for kw in keywords:
            if kw in comment_lower:
                return cat
    return 'General'

def predict_comment(comment):
    # Detect language
    try:
        lang = detect(comment)
    except:
        lang = 'en'

    if lang == 'ko':
        # Simple Korean keyword check
        score = 90  # assign high score for Korean keywords
        category = get_category(comment)
        return f"Toxic Comment 🚫 | Toxicity Score: {score}% | Category: {category}" if category != 'General' else f"Safe Comment ✅ | Toxicity Score: 10% | Category: General"
    else:
        # English: use trained model
        vec = vectorizer.transform([comment])
        prob = model.predict_proba(vec)[0][1]
        score = round(prob * 100,2)
        category = get_category(comment)
        return f"Toxic Comment 🚫 | Toxicity Score: {score}% | Category: {category}" if prob > 0.5 else f"Safe Comment ✅ | Toxicity Score: {score}% | Category: {category}"
    
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ============================================================
# 1. LOAD DATA FROM data.json
# ============================================================

with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

STORE    = DATA["store_info"]
PRODUCTS = DATA["products"]
FAQ      = DATA["faq"]

# ============================================================
# 2. PREPROCESSING
# ============================================================

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ============================================================
# 3. TF-IDF ENGINE
# ============================================================

faq_questions = [preprocess(item["question"]) for item in FAQ]
faq_answers   = [item["answer"] for item in FAQ]

vectorizer   = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(faq_questions)

def tfidf_search(user_input: str, threshold: float = 0.15):
    processed = preprocess(user_input)
    user_vec  = vectorizer.transform([processed])
    scores    = cosine_similarity(user_vec, tfidf_matrix)
    best_idx  = scores.argmax()
    best_score = scores[0][best_idx]
    if best_score >= threshold:
        return faq_answers[best_idx]
    return None

# ============================================================
# 4. INTENT DETECTION
# ============================================================

INTENTS = {
    "GET_PRICE": [
        "prix", "combien", "شحال", "bkam", "coute", "tarif"
    ],
    "CHECK_STOCK": [
        "dispo", "disponible", "kayen", "عندكم", "stock",
        "wach kayen", "avez", "reste"
    ],
    "GET_SIZES": [
        "taille", "pointure", "size", "قياس", "mesure"
    ],
    "GET_COLORS": [
        "couleur", "color", "لون", "existe en"
    ],
    "HOW_TO_ORDER": [
        "commander", "commande", "acheter", "كيفاش نطلب", "order"
    ],
    "GREET": [
        "salam", "bonjour", "hello", "bonsoir", "ahlan", "مرحبا", "hi"
    ],
    "THANKS": [
        "merci", "شكرا", "thank", "barak", "شكراً"
    ],
}

def detect_intent(text: str) -> str:
    text_lower = text.lower()
    for intent, keywords in INTENTS.items():
        if any(kw in text_lower for kw in keywords):
            return intent
    return "GENERAL"

# ============================================================
# 5. ENTITY DETECTION
# ============================================================

PRODUCT_KEYWORDS = {
    "tshirt":    ["tshirt", "t-shirt", "chemise", "تيشيرت"],
    "jean":      ["jean", "jeans", "pantalon", "جان", "بنطلون"],
    "veste":     ["veste", "jacket", "blouson", "جاكيت"],
    "robe":      ["robe", "روب", "فستان"],
    "chaussure": ["chaussure", "shoes", "basket", "sneaker", "حذاء", "شوز"],
}

def detect_product(text: str):
    text_lower = text.lower()
    for product_key, keywords in PRODUCT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return product_key
    return None

# ============================================================
# 6. RESPONSE BUILDER
# ============================================================

def build_response(intent: str, product_key: str, user_input: str) -> str:

    if intent == "GREET":
        return (
            f"👋 Salam! Bienvenue chez {STORE['nom']}!\n"
            "Comment je peux vous aider?\n"
            "• Prix d'un produit\n"
            "• Stock disponible\n"
            "• Tailles / Couleurs\n"
            "• Comment commander"
        )

    if intent == "THANKS":
        return f"😊 Avec plaisir! N'hésitez pas si vous avez d'autres questions."

    if intent == "GET_PRICE":
        if product_key:
            p = PRODUCTS[product_key]
            stock = "✅ En stock" if p["stock"] else "❌ Rupture de stock"
            return f"💰 {p['nom']}: {p['prix']} DA\n{stock}"
        lines = [f"💰 Prix chez {STORE['nom']}:\n"]
        for p in PRODUCTS.values():
            icon = "✅" if p["stock"] else "❌"
            lines.append(f"{icon} {p['nom']}: {p['prix']} DA")
        return "\n".join(lines)

    if intent == "CHECK_STOCK":
        if product_key:
            p = PRODUCTS[product_key]
            if p["stock"]:
                return f"✅ {p['nom']} est disponible! Prix: {p['prix']} DA"
            return (
                f"❌ {p['nom']} est en rupture de stock.\n"
                f"📱 Contactez-nous: {STORE['whatsapp']}"
            )
        return "❓ De quel produit vous parlez?"

    if intent == "GET_SIZES":
        if product_key:
            p = PRODUCTS[product_key]
            tailles = " | ".join(p["tailles"])
            return f"📏 Tailles {p['nom']}:\n{tailles}"
        return "📏 Pour quel produit vous cherchez la taille?"

    if intent == "GET_COLORS":
        if product_key:
            p = PRODUCTS[product_key]
            couleurs = " | ".join(p["couleurs"])
            return f"🎨 Couleurs {p['nom']}:\n{couleurs}"
        return "🎨 Pour quel produit vous cherchez la couleur?"

    if intent == "HOW_TO_ORDER":
        return (
            "🛒 Pour commander:\n"
            "1. Produit\n"
            "2. Taille\n"
            "3. Couleur\n"
            "4. Adresse\n\n"
            f"📱 WhatsApp: {STORE['whatsapp']}"
        )

    faq_result = tfidf_search(user_input)
    if faq_result:
        return faq_result

    return (
        "🤔 Je n'ai pas compris.\n"
        "Vous pouvez demander:\n"
        "• Prix / Stock / Tailles\n"
        "• Livraison / Paiement\n"
        "• Comment commander\n\n"
        f"📱 WhatsApp: {STORE['whatsapp']}"
    )

# ============================================================
# 7. MAIN FUNCTION
# ============================================================

def get_bot_response(user_input: str) -> str:
    if not user_input or not user_input.strip():
        return "Veuillez écrire votre question 😊"
    intent      = detect_intent(user_input)
    product_key = detect_product(user_input)
    return build_response(intent, product_key, user_input)
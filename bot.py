import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ============================================================
# 1. DATA — products + FAQ
# ============================================================

# منتجات المتجر — تبدل بمنتجاتك الحقيقية
PRODUCTS = {
    "tshirt":   {"prix": 1200, "nom": "T-shirt",   "stock": True,  "tailles": ["S","M","L","XL"]},
    "jean":     {"prix": 3500, "nom": "Jean",       "stock": True,  "tailles": ["38","40","42","44"]},
    "veste":    {"prix": 5500, "nom": "Veste",      "stock": False, "tailles": ["M","L","XL"]},
    "robe":     {"prix": 2800, "nom": "Robe",       "stock": True,  "tailles": ["S","M","L"]},
    "chaussure":{"prix": 4200, "nom": "Chaussure",  "stock": True,  "tailles": ["39","40","41","42","43"]},
}

# أسئلة عامة (FAQ) — TF-IDF
FAQ = [
    {"question": "livraison",                  "answer": "🚚 Livraison gratuite dès 5000 DA. Délai: 2-3 jours."},
    {"question": "paiement",                   "answer": "💳 Paiement à la livraison ou virement CCP."},
    {"question": "retour echange",             "answer": "🔄 Retour/échange dans les 7 jours. Produit non utilisé."},
    {"question": "horaire",                    "answer": "🕘 On est dispo 9h-21h tous les jours."},
    {"question": "contact whatsapp",           "answer": "📱 WhatsApp: 05 XX XX XX XX"},
    {"question": "adresse",                    "answer": "📍 Oran, Bir El Djir — livraison partout en Algérie."},
    {"question": "commande suivi",             "answer": "📦 Envoyez votre numéro de commande sur WhatsApp."},
    {"question": "promotion reduction",        "answer": "🎉 Suivez notre page pour les promos!"},
    {"question": "cadeau emballage",           "answer": "🎁 Oui, emballage cadeau disponible sur demande."},
    {"question": "qualite matiere tissu",      "answer": "✅ Tous nos produits sont de haute qualité — garantis."},
    {"question": "taille guide comment choisir","answer": "📏 Envoyez vos mesures sur WhatsApp, on vous guide."},
    {"question": "couleur disponible",         "answer": "🎨 Dites-nous le produit, on vous envoie les couleurs dispo."},
    {"question": "commande comment",           "answer": "🛒 Envoyez: Produit + Taille + Adresse sur WhatsApp."},
]

# ============================================================
# 2. PREPROCESSING
# ============================================================

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)   # remove punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ============================================================
# 3. TF-IDF ENGINE (للأسئلة العامة)
# ============================================================

faq_questions = [preprocess(item["question"]) for item in FAQ]
faq_answers   = [item["answer"] for item in FAQ]

vectorizer   = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(faq_questions)

def tfidf_search(user_input: str, threshold: float = 0.15) -> str | None:
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
        "prix", "combien", "شحال", "bkam", "coute",
        "tarif", "cout", "cher", "budget", "coût"
    ],
    "CHECK_STOCK": [
        "dispo", "disponible", "kayen", "عندكم", "stock",
        "wach kayen", "avez", "reste", "rupture"
    ],
    "GET_SIZES": [
        "taille", "pointure", "size", "قياس", "mesure",
        "xs", "small", "medium", "large", "xl"
    ],
    "HOW_TO_ORDER": [
        "commander", "commande", "acheter", "كيفاش نطلب",
        "order", "achat"
    ],
    "GREET": [
        "salam", "bonjour", "hello", "bonsoir", "ahlan",
        "مرحبا", "ازيك", "hi"
    ],
    "THANKS": [
        "merci", "شكرا", "شكراً", "thank", "barak",
        "سلام عليك", "وعليكم"
    ],
}

def detect_intent(text: str) -> str:
    text_lower = text.lower()
    for intent, keywords in INTENTS.items():
        if any(kw in text_lower for kw in keywords):
            return intent
    return "GENERAL"

# ============================================================
# 5. ENTITY DETECTION (المنتج)
# ============================================================

PRODUCT_KEYWORDS = {
    "tshirt":    ["tshirt", "t-shirt", "chemise", "tricot", "تيشيرت"],
    "jean":      ["jean", "jeans", "pantalon", "جان", "بنطلون"],
    "veste":     ["veste", "jacket", "blouson", "veston", "جاكيت", "بلوزة"],
    "robe":      ["robe", "روب", "فستان"],
    "chaussure": ["chaussure", "shoes", "shoe", "pointure",
                  "basket", "sneaker", "soulier", "حذاء", "شوز"],
}

def detect_product(text: str) -> str | None:
    text_lower = text.lower()
    for product_key, keywords in PRODUCT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return product_key
    return None

# ============================================================
# 6. RESPONSE BUILDER
# ============================================================

def build_response(intent: str, product_key: str | None, user_input: str) -> str:

    # --- Greet ---
    if intent == "GREET":
        return (
            "👋 Salam! Bienvenue dans notre boutique!\n"
            "Comment je peux vous aider?\n"
            "• Prix d'un produit\n"
            "• Stock disponible\n"
            "• Comment commander"
        )

    # --- Thanks ---
    if intent == "THANKS":
        return "😊 Avec plaisir! N'hésitez pas si vous avez d'autres questions."

    # --- Prix ---
    if intent == "GET_PRICE":
        if product_key:
            p = PRODUCTS[product_key]
            return (
                f"💰 Prix du {p['nom']}: **{p['prix']} DA**\n"
                f"{'✅ En stock' if p['stock'] else '❌ Rupture de stock'}"
            )
        # Prix sans produit spécifié
        lines = ["💰 Voici nos prix:\n"]
        for key, p in PRODUCTS.items():
            stock_icon = "✅" if p["stock"] else "❌"
            lines.append(f"{stock_icon} {p['nom']}: {p['prix']} DA")
        return "\n".join(lines)

    # --- Stock ---
    if intent == "CHECK_STOCK":
        if product_key:
            p = PRODUCTS[product_key]
            if p["stock"]:
                return f"✅ Oui, le {p['nom']} est disponible! Prix: {p['prix']} DA"
            else:
                return (
                    f"❌ Désolé, le {p['nom']} est en rupture de stock.\n"
                    "Envoyez-nous un message sur WhatsApp pour être notifié."
                )
        return "❓ De quel produit vous parlez? (T-shirt, Jean, Veste, Robe, Chaussure)"

    # --- Tailles ---
    if intent == "GET_SIZES":
        if product_key:
            p = PRODUCTS[product_key]
            tailles = " | ".join(p["tailles"])
            return f"📏 Tailles disponibles pour {p['nom']}:\n{tailles}"
        return "📏 Pour quelle article vous cherchez la taille?"

    # --- Commander ---
    if intent == "HOW_TO_ORDER":
        return (
            "🛒 Pour commander, envoyez-nous sur WhatsApp:\n"
            "1. Nom du produit\n"
            "2. Taille\n"
            "3. Couleur\n"
            "4. Votre adresse\n\n"
            "📱 WhatsApp: 05 XX XX XX XX"
        )

    # --- General: TF-IDF ---
    faq_result = tfidf_search(user_input)
    if faq_result:
        return faq_result

    # --- Fallback ---
    return (
        "🤔 Désolé, je n'ai pas compris votre question.\n"
        "Vous pouvez me demander:\n"
        "• Prix d'un produit\n"
        "• Stock disponible\n"
        "• Tailles disponibles\n"
        "• Livraison / Paiement\n"
        "• Comment commander\n\n"
        "Ou contactez-nous sur WhatsApp: 05 XX XX XX XX"
    )

# ============================================================
# 7. MAIN FUNCTION — تستعمل هاد الفونكسيون في FastAPI
# ============================================================

def get_bot_response(user_input: str) -> str:
    if not user_input or not user_input.strip():
        return "Veuillez écrire votre question 😊"

    intent      = detect_intent(user_input)
    product_key = detect_product(user_input)
    response    = build_response(intent, product_key, user_input)

    return response


# ============================================================
# 8. TEST LOCAL — تحذفه من بعد
# ============================================================

if __name__ == "__main__":
    tests = [
        "Salam!",
        "prix tshirt",
        "wach kayen jean ?",
        "شحال الveste",
        "taille chaussure",
        "كيفاش نطلب",
        "livraison gratuite ?",
        "merci barak",
        "prix",               # بدون منتج — يرجع كل الأسعار
        "wach kayen veste",   # rupture de stock
        "blabla xyz ???",     # fallback
    ]

    print("=" * 50)
    for q in tests:
        print(f"\n❓ {q}")
        print(f"✅ {get_bot_response(q)}")
    print("\n" + "=" * 50)
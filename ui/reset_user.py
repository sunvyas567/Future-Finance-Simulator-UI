from streamlit_authenticator.utilities.hasher import Hasher
from app.core.firebase import get_db

db = get_db()

username = "amvyas"  # 👈 change this
new_password = "Temp@1234"  # 👈 give user once, force change later

hashed = Hasher.hash(new_password)

db.collection("users").document(username).update({
    "password": hashed
})

print("✅ Password reset for", username)

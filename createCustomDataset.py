import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import re
import javalang
from get_CAT import generate_code_aligned_type_sequence

# Firebase Initialization
if not firebase_admin._apps:
    firebase_creds = st.secrets["firebase"]
    cred = credentials.Certificate(firebase_creds)  # Path to your private key
    firebase_admin.initialize_app(cred)

# Firestore database
db = firestore.client()

# Firestore collection and document
COLLECTION_NAME = 'datasets'
DOCUMENT_NAME = 'customData'

def process_source(code):
    """Removes comments, tokenizes the Java source code, and replaces literals and data types with placeholders."""
    code = re.sub(r'//.*', '', code)  # Remove single-line comments
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)  # Remove multi-line comments
    code = code.replace('\n', ' ').strip()  # Remove newlines
    tokens = list(javalang.tokenizer.tokenize(code))  # Tokenize
    tks = []
    for tk in tokens:
        if tk.__class__.__name__ == 'String' or tk.__class__.__name__ == 'Character':
            tks.append('STR_')
        elif 'Integer' in tk.__class__.__name__ or 'FloatingPoint' in tk.__class__.__name__:
            tks.append('NUM_')
        elif tk.__class__.__name__ == 'Boolean':
            tks.append('BOOL_')
        else:
            tks.append(tk.value)
    return " ".join(tks)

def add_to_dataset(code, comment):
    """Processes the code, generates the CAT, and saves the entry to Firebase Firestore."""
    processed_code = process_source(code)
    try:
        cat = generate_code_aligned_type_sequence(processed_code)
    except Exception as e:
        st.error(f"Error generating CAT: {str(e)}")
        return False

    entry = {
        "code": processed_code,
        "CAT": cat,
        "comment": comment
    }

    # Add data to Firestore
    try:
        # Get the existing document
        doc_ref = db.collection(COLLECTION_NAME).document(DOCUMENT_NAME)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            if 'entries' in data:
                data['entries'].append(entry)
            else:
                data['entries'] = [entry]
        else:
            data = {'entries': [entry]}

        # Update Firestore document
        doc_ref.set(data)
        st.success("Data successfully added to the Firebase Firestore!")
    except Exception as e:
        st.error(f"Error saving to Firebase Firestore: {str(e)}")
        return False

# Streamlit UI
st.title("Java Code Dataset Builder")

st.write("Enter the Java code snippet and its corresponding comment to add it to the shared Firebase Firestore dataset.")

java_code = st.text_area("Paste Java Code Here", height=200, placeholder="Enter your Java code here...")
comment = st.text_area("Enter Comment Here", height=100, placeholder="Enter the comment for the Java code...")

if st.button("Add to Dataset"):
    if not java_code.strip():
        st.warning("Please enter the Java code.")
    elif not comment.strip():
        st.warning("Please enter a comment for the code.")
    else:
        add_to_dataset(java_code, comment)

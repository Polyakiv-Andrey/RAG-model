import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle

# Load CSV without headers first
df = pd.read_csv(
    "/Users/bvoloshy/PycharmProjects/RAG-model/data/FedRAMP_High_Security_Controls.csv",
    header=None,
    skiprows=2  # Skipping two header rows explicitly
)

# Assign correct column names explicitly
df.columns = [
    "Count", "SortID", "Family", "ControlID", "ControlName",
    "ControlDescription", "FedRAMPHighBaseline", "Justification",
    "FedRAMPDefinedAssignment", "AdditionalFedRAMPRequirements", "FedRAMPParameter"
]

# Remove rows without a valid ControlID
df = df[df["ControlID"].notnull() & (df["ControlID"] != "")]

# Combine necessary columns into a single content field
df["content"] = df["ControlID"] + " - " + df["ControlName"] + " - " + df["ControlDescription"]

# Load local embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embeddings
embeddings = model.encode(df["content"].tolist(), convert_to_numpy=True)

# Create and populate FAISS index
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# Save FAISS index
faiss.write_index(index, "local_fedramp.index")

# Save content for retrieval
with open("local_fedramp_contents.pkl", "wb") as f:
    pickle.dump(df["content"].tolist(), f)

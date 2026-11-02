
from huggingface_hub import hf_hub_download
import pandas as pd

REPO_ID = "NextGig-Rocks/global-job-postings-multi-ats"
FILE_NAME = "nextgig_jobs_2026-06.parquet"

print("Downloading dataset...")

file_path = hf_hub_download(
    repo_id=REPO_ID,
    filename=FILE_NAME,
    repo_type="dataset"
)

print("Dataset downloaded:", file_path)

df = pd.read_parquet(file_path)

print("\nDataset shape:", df.shape)

print("\nAll columns:")
for column in df.columns:
    print(column)

print("\nFirst 3 records:")
print(df.head(3).to_string())

print("\nMissing values:")
print(df.isnull().sum().sort_values(ascending=False))

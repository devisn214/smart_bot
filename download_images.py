import os
import requests
from PIL import Image
from io import BytesIO
import pandas as pd

# Load Amazon product dataset
amazon_data = pd.read_csv('data/amazon-products.csv')  # Update the path if needed

# Directory to store downloaded images
image_dir = "data/downloaded_images"
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

# Function to download and save image
def download_image(image_url, product_title):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        # Create a safe file name based on the product title
        file_name = f"{product_title[:50].replace(' ', '_')}.jpg"  # Limit the file name length
        file_path = os.path.join(image_dir, file_name)
        img.save(file_path)
        return file_path
    except Exception as e:
        print(f"Error downloading {image_url}: {e}")
        return None

# Download all product images
def download_all_images():
    for idx, row in amazon_data.iterrows():
        image_url = row['image_url']
        if pd.notna(image_url):
            file_path = download_image(image_url, row['title'])
            if file_path:
                print(f"Downloaded: {file_path}")

if __name__ == "__main__":
    download_all_images()

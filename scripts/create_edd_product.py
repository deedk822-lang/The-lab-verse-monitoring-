import os
import base64
import requests
import json

def create_edd_product(title, price, description, file_path):
    """
    Creates a new digital product in Easy Digital Downloads on a WordPress site.
    """
    wordpress_url = os.getenv("WORDPRESS_URL")
    wordpress_user = os.getenv("WORDPRESS_USER")
    wordpress_app_password = os.getenv("WORDPRESS_APP_PASSWORD")

    if not all([wordpress_url, wordpress_user, wordpress_app_password]):
        print("Error: WordPress environment variables (WORDPRESS_URL, WORDPRESS_USER, WORDPRESS_APP_PASSWORD) not set.")
        return None

    # Step 1: Upload the file to the WordPress Media Library
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None


    credentials = f"{wordpress_user}:{wordpress_app_password}"
    token = base64.b64encode(credentials.encode())
    headers = {
        'Authorization': f'Basic {token.decode("utf-8")}',
        'Content-Disposition': f'attachment; filename={os.path.basename(file_path)}',
    }

    upload_url = f"{wordpress_url}/wp-json/wp/v2/media"
    print(f"Uploading file to {upload_url}...")
    upload_response = requests.post(upload_url, headers=headers, data=file_data, timeout=30)

    if upload_response.status_code not in [200, 201]:
        print(f"Error uploading file. Status: {upload_response.status_code}")
        print(f"Response: {upload_response.text}")
        return None

    media_data = upload_response.json()
    attachment_id = media_data.get('id')
    if not attachment_id:
        print("Error: Could not get attachment ID from upload response.")
        return None


    print(f"File uploaded successfully. Media ID: {attachment_id}")

    # Step 2: Create the EDD product
    product_data = {
        "title": title,
        "content": description,
        "status": "publish",
        "meta": {
            "edd_price": str(price),
            "edd_download_files": [
                {
                    "attachment_id": str(attachment_id),
                    "name": os.path.basename(file_path)
                }
            ]
        }
    }

    product_url = f"{wordpress_url}/wp-json/wp/v2/downloads"
    product_headers = {
        'Authorization': f'Basic {token.decode("utf-8")}',
        'Content-Type': 'application/json'
    }

    print(f"Creating product '{title}'...")
    product_response = requests.post(product_url, headers=product_headers, data=json.dumps(product_data), timeout=30)

    if product_response.status_code in [200, 201]:
        print("Product created successfully!")
        return product_response.json()
    else:
        print(f"Error creating product. Status: {product_response.status_code}")
        print(f"Response: {product_response.text}")
        return None

if __name__ == "__main__":
    # This is an example of how to use the function.
    # In a real scenario, you would call this function with dynamic data.
    print("Running example: creating a dummy digital product...")

    # Create a dummy file for upload
    DUMMY_FILE = "example_product.py"
    with open(DUMMY_FILE, "w") as f:
        f.write("print('This is a sample Python script sold as a digital product.')")

    # Set dummy environment variables if they are not present for the example
    if "WORDPRESS_URL" not in os.environ:
        print("WORDPRESS_URL not set. Please set it to run the example.")
    else:
        new_product = create_edd_product(
            title="AI-Generated Python Tool",
            price="29.99",
            description="A powerful, AI-generated Python script for automating daily tasks. This is a sample product created via the REST API.",
            file_path=DUMMY_FILE
        )
        if new_product:
            print("\n--- New Product Details ---")
            print(f"ID: {new_product.get('id')}")
            print(f"Link: {new_product.get('link')}")
            print("---------------------------\n")

    # Clean up the dummy file
    os.remove(DUMMY_FILE)
    print("Example finished.")
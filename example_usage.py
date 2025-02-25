from gs1_digital_assets import GS1DigitalAssets

def main():
    # Initialize the client with your credentials
    client = GS1DigitalAssets(
        client_id="your_client_id",
        client_secret="your_client_secret",
        username="your_username",
        password="your_password"
    )

    try:
        # Upload an image
        result = client.upload_image(
            image_path="path/to/your/image.jpg",
            information_provider_gln="your_gln",
            target_market_country_code="752"  # Example: Sweden
        )
        
        print("Upload successful!")
        print("Asset IDs:", result["AssetIds"])

        # Check status of the uploaded asset
        for asset_id in result["AssetIds"]:
            status = client.get_asset_status(asset_id)
            print(f"Asset {asset_id} status:", status)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
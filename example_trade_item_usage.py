from gs1_trade_item import GS1TradeItem

def main():
    # Initialize the client with your credentials
    client = GS1TradeItem(
        client_id="your_client_id",
        client_secret="your_client_secret",
        username="your_username",
        password="your_password"
    )

    try:
        # Get information for a specific GTIN
        gtin_info = client.get_item_by_gtin(
            gtin="07309622201028",
            information_provider_gln="7350076480033"
        )
        print("Trade Item Information:", gtin_info)

        # Verify multiple GTINs
        gtins_to_verify = ["07309622201028", "07309622201035"]
        verification_result = client.verify_gtins(gtins_to_verify)
        print("Verification Results:", verification_result)

        # Search for trade items with specific parameters
        search_params = {
            "informationProviderGlns": ["7350076480033"],
            "itemStatus": ["published"],
            "itemTypes": ["Base"],
            "onlyCurrentVersion": True,
            "limit": 10
        }
        search_results = client.search_trade_items(search_params)
        print("Search Results:", search_results)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
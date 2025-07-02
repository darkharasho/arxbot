import time
from src.models.api_key import ApiKey
from src.gw2_api_client import GW2ApiClient
from peewee import DoesNotExist
from tqdm import tqdm  # <-- Progress bar

SLEEP_SECONDS = 2  # Adjust as needed to avoid rate limits

def get_guild_names_for_key(api_key_value):
    client = GW2ApiClient(api_key=api_key_value)
    try:
        account = client.account()
        guild_ids = account.get("guilds", [])
        guild_names = []
        for guild_id in guild_ids:
            try:
                guild_info = client.guild(gw2_guild_id=guild_id)
                if isinstance(guild_info, dict):
                    name = guild_info.get("name")
                    if name:
                        guild_names.append(name)
            except Exception as e:
                print(f"Failed to fetch guild info for {guild_id}: {e}")
            time.sleep(SLEEP_SECONDS)
        return guild_names
    except Exception as e:
        print(f"Failed to fetch account for API key: {e}")
        return []

def main():
    api_keys = list(ApiKey.select())
    for api_key in tqdm(api_keys, desc="Populating guild names"):
        print(f"Processing ApiKey id={api_key.id}...")
        guild_names = get_guild_names_for_key(api_key.value)
        print(f"  Found guilds: {guild_names}")
        api_key.guild_names = guild_names
        api_key.save()
        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    main()
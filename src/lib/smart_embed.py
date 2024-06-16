import discord
import json
import re

class SmartEmbed:
    def __init__(self, title="", description="", color=discord.Color.blue()):
        self.title = title
        self.description = description
        self.color = color
        self.fields = []
        self.max_field_length = 1024
        self.embeds = []

    def add_field(self, name, value, value_type="string", inline=False):
        if value_type == "dict":
            if isinstance(value, str):
                try:
                    # Handle multiple JSON objects in a single string
                    json_objects = value.strip().split("\n")
                    value = [self.convert_to_valid_json(obj) for obj in json_objects if obj.strip()]
                except json.JSONDecodeError:
                    value = [{"error": "Invalid JSON string"}]
            else:
                value = [value]
            self.add_dict_fields(name, value, inline)
        else:
            self.fields.append((name, value, value_type, inline))

    def convert_to_valid_json(self, string):
        # Convert single quotes to double quotes and handle nested quotes properly
        string = re.sub(r"(\w+)(?=\s*:)", r'"\1"', string)  # Convert keys to double quotes
        string = re.sub(r"'(.*?)'", r'"\1"', string)  # Convert values to double quotes
        return json.loads(string)

    def add_dict_fields(self, name, dict_values, inline):
        for value in dict_values:
            value_str = json.dumps(value, indent=4, sort_keys=True, default=str)
            if len(value_str) + 6 > self.max_field_length:  # Account for code block markers
                max_chunk_size = self.max_field_length - 6
                chunks = self.split_string_into_chunks(value_str, max_chunk_size)
                for i, chunk in enumerate(chunks):
                    chunk_value = f"```json\n{chunk}```" if i == 0 else chunk
                    self.fields.append((name if i == 0 else f"{name} (cont.)", chunk_value, "dict", inline))
            else:
                value_str = f"```json\n{value_str}```"
                self.fields.append((name, value_str, "dict", inline))

    def split_string_into_chunks(self, text, max_chunk_size):
        """Splits a long string into chunks of max_chunk_size characters."""
        return [text[i:i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]

    def create_embeds(self):
        current_embed = discord.Embed(title=self.title, description=self.description, color=self.color)
        total_length = len(self.title) + len(self.description)

        for name, value, value_type, inline in self.fields:
            if len(value) > self.max_field_length:
                max_chunk_size = self.max_field_length - 6  # Account for code block markers
                value = value[7:-3]  # Remove existing code block markers for proper splitting
                chunks = self.split_string_into_chunks(value, max_chunk_size)
                for i, chunk in enumerate(chunks):
                    chunk_value = f"```json\n{chunk}\n```" if value_type == "dict" else chunk
                    if i == 0:
                        field_name = name
                    else:
                        field_name = f"{name} (cont.)"
                    if len(current_embed.fields) == 25 or total_length + len(chunk_value) > 6000:
                        self.embeds.append(current_embed)
                        current_embed = discord.Embed(color=self.color)
                        total_length = 0
                    current_embed.add_field(name=field_name, value=chunk_value, inline=inline)
                    total_length += len(field_name) + len(chunk_value)
            else:
                if len(current_embed.fields) == 25 or total_length + len(value) > 6000:
                    self.embeds.append(current_embed)
                    current_embed = discord.Embed(color=self.color)
                    total_length = 0
                current_embed.add_field(name=name, value=value, inline=inline)
                total_length += len(name) + len(value)

        self.embeds.append(current_embed)
        return self.embeds

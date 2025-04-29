import os
import json
from django.core.management.base import BaseCommand
from pymongo import MongoClient

class Command(BaseCommand):
    help = 'Automatically imports Chinook JSON data into MongoDB.'

    def handle(self, *args, **kwargs):
        client = MongoClient('mongodb://mongodb:27017/')
        db = client['chinook']

        base_path = 'data/chinook'

        # Exact filenames from your provided directory listing
        json_files = {
            'Album.json': 'Album',
            'Artist.json': 'Artist',
            'Customer.json': 'Customer',
            'Employee.json': 'Employee',
            'Genre.json': 'Genre',
            'Invoice.json': 'Invoice',
            'InvoiceLine.json': 'InvoiceLine',
            'MediaType.json': 'MediaType',
            'Playlist.json': 'Playlist',
            'PlaylistTrack.json': 'PlaylistTrack',
            'Track.json': 'Track'
        }

        for file_name, collection_name in json_files.items():
            collection = db[collection_name]

            if collection.count_documents({}) > 0:
                self.stdout.write(self.style.WARNING(
                    f"Collection '{collection_name}' already exists, skipping import."))
                continue

            file_path = os.path.join(base_path, file_name)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    if not isinstance(data, list):
                        self.stdout.write(self.style.ERROR(
                            f"Expected a list in '{file_name}', got {type(data)}."))
                        continue

                    collection.insert_many(data)
                    self.stdout.write(self.style.SUCCESS(
                        f"Imported {len(data)} documents into '{collection_name}'."))
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(
                    f"File '{file_name}' not found in '{base_path}'."))
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(
                    f"JSON decode error in '{file_name}': {e}"))

        self.stdout.write(self.style.SUCCESS("Data import completed successfully."))

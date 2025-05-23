def load_data_to_database(file_path, db_name):
    """Laad data vanuit een CSV-bestand naar de SQLite-database in chunks."""
    conn = sqlite3.connect(db_name)

    chunksize = 100000  # Verwerk 100.000 rijen per keer
    try:
        for chunk in pd.read_csv(
            file_path,
            sep=";",  # Gebruik puntkomma als scheidingsteken
            usecols=["datum", "tijdstip", "product", "aantal", "verkoopprijs"],  # Lees alleen de relevante kolommen
            chunksize=chunksize,
        ):
            # Verwijder eventuele extra spaties rondom kolomnamen
            chunk.columns = chunk.columns.str.strip()

            # Corrigeer de verkoopprijs (vervang komma's door punten en zet om naar float)
            chunk["verkoopprijs"] = chunk["verkoopprijs"].str.replace(",", ".").astype(float)

            # Verwijder rijen met ontbrekende waarden in verplichte kolommen
            chunk = chunk.dropna(subset=["datum", "tijdstip", "product", "aantal", "verkoopprijs"])

            # Controleer dat kolommen de juiste types hebben
            chunk["aantal"] = chunk["aantal"].astype(int)

            # Schrijf de chunk naar de database
            chunk.to_sql("sales", conn, if_exists="append", index=False)
            print(f"Chunk van {chunksize} rijen geladen.")
    except Exception as e:
        print(f"Fout tijdens laden van data: {e}")

    conn.close()

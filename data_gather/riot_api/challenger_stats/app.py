import json
from challenger_match_data import MatchData

def merge_data(existing_data, new_data):
    if isinstance(existing_data, list) and isinstance(new_data, list):
        return existing_data + new_data
    elif isinstance(existing_data, dict) and isinstance(new_data, dict):
        for key in new_data:
            if key in existing_data:
                existing_data[key] = merge_data(existing_data[key], new_data[key])
            else:
                existing_data[key] = new_data[key]
        return existing_data
    else:
        return new_data

def main():
    md = MatchData()
    challenger_data = md.fetch_challenger_data()

    # Read existing data from the JSON file
    try:
        with open('test-output.json', 'r') as infile:
            existing_data = json.load(infile)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = None

    # Merge the existing data with the new data
    if existing_data is not None:
        combined_data = merge_data(existing_data, challenger_data)
    else:
        combined_data = challenger_data

    # Write the combined data back to the JSON file
    with open('test-output.json', 'w') as outfile:
        json.dump(combined_data, outfile, indent=4)

if __name__ == '__main__':
    main()

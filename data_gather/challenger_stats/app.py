from challenger_match_data import MatchData

def main():
    md = MatchData()
    challenger_data = md.fetch_challenger_data()
    print(challenger_data)

if __name__ == '__main__':
    main()
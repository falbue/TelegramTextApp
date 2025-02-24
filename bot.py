import config

if __name__ == "__main__":
    from TelegramTextApp import TTA
    TTA.start(config.API, "test.json", debug=True)
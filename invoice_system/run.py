from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        debug=False,
        host=app.config["APP_HOST"],
        port=app.config["APP_PORT"],
    )

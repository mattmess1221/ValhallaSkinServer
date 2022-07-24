import valhalla

app = valhalla.create_app("config.DebugConfig")

if __name__ == "__main__":
    app.run(debug=True)

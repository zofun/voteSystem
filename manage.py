from vote import get_app

app = get_app('develop')

if __name__ == '__main__':
    print(app.url_map)
    app.run()

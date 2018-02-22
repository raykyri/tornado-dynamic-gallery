import os
import sys
import time
import datetime

import tornado.ioloop
import tornado.web
import tornado.websocket

# for ImageProcessingService
from PIL import Image, ImageEnhance, ImageOps

# for ImageWatcherWebSocket
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PORT = 8000
NUM_SUBPROCESSES = 1

def unique_filename():
    return str(datetime.datetime.now().date()).replace('-', '') + \
        str(datetime.datetime.now().time()).replace(':', '').replace('.', '')

#
# ImageProcessingService
#

class ImageProcessingService(tornado.web.RequestHandler):
    def post(self):
        files = self.request.files.get("file")
        for file in files:
            print "Processing {}".format(file["filename"])

            # Convert file from in-memory string to PIL image
            upload_body = file["body"]
            new_filename = unique_filename()
            with open("tmp/" + new_filename + ".temp", "wb") as temp_file:
                temp_file.write(file["body"])
            img = Image.open("tmp/" + new_filename + ".temp")

            # Apply filters to image, and save
            RECOLOR_BLACK_TO = (42, 35, 29)
            RECOLOR_WHITE_TO = (255, 255, 255)
            img = ImageOps.colorize(img.convert(mode="L"), RECOLOR_BLACK_TO, RECOLOR_WHITE_TO)

            CROP_WIDTH = 400
            CROP_HEIGHT = 600
            img = ImageOps.fit(img, (CROP_WIDTH, CROP_HEIGHT), Image.ANTIALIAS, 0, (0.5, 0.5))

            img.save("gallery/" + new_filename + ".jpg")
            print "Saved as {}.jpg".format(new_filename)

        self.write("Success")

#
# ImageWatcherWebSocket
#

class ImageWatcherEventHandler(FileSystemEventHandler):
    def __init__(self, event_callback):
        self.event_callback = event_callback

    def on_created(self, event):
        self.event_callback()

class ImageWatcher():
    def __init__(self):
        self.callbacks = {}
        self.registered_callbacks_counter = 0
        event_handler = ImageWatcherEventHandler(event_callback=self.invoke_callbacks)
        self.watchdog_observer = Observer()
        self.watchdog_observer.schedule(event_handler, "gallery", recursive=True)
        self.watchdog_observer.start()

    def register_callback(self, callback):
        self.callbacks[self.registered_callbacks_counter] = callback
        self.registered_callbacks_counter += 1
        print "Registered callback, now there are", len(self.callbacks.items())
        return self.registered_callbacks_counter - 1

    def deregister_callback(self, index):
        del self.callbacks[index]
        print "Deregistered callback, now there are", len(self.callbacks.items())

    def invoke_callbacks(self):
        print "Invoking callbacks, there are", len(self.callbacks.items())
        for fn in self.callbacks.values():
            fn()

watcher = ImageWatcher()

class ImageWatcherWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print "WebSocket opened"

        def ws_write():
            gallery_contents = os.listdir("gallery")
            response = ",".join([name for name in gallery_contents if name.endswith(".jpg")])
            self.write_message(response, binary=False)
            print "WebSocket sent file listing to client"
        ws_write()
        self.watcher_callback_index = watcher.register_callback(ws_write)

    def on_close(self):
        watcher.deregister_callback(self.watcher_callback_index)
        print "WebSocket closed"

    def on_message(self, message):
        print "WebSocket received a message (should never happen)"
        pass

#
# Tornado application
#

class IndexPage(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/index.html")

if __name__ == "__main__":
    application = tornado.web.Application([
        # Services
        (r"/upload", ImageProcessingService),
        (r"/websocket", ImageWatcherWebSocket),
        # Static servers (TODO: These files shouldn't be in the root directory)
        (r"/(favicon\.ico)", tornado.web.StaticFileHandler, {"path": "."}),
        (r"/(robots\.txt)", tornado.web.StaticFileHandler, {"path": "."}),
        (r"/gallery/(.*)", tornado.web.StaticFileHandler, {"path": "gallery"}),
        (r"/assets/(.*)", tornado.web.StaticFileHandler, {"path": "assets"}),
        (r"/", IndexPage),
    ])

    sys.stdout.write("Starting server at http://localhost:{}/\n".format(PORT))
    sys.stdout.flush()
    server = tornado.httpserver.HTTPServer(application)
    server.bind(PORT)
    server.start(NUM_SUBPROCESSES) # Specify number of subprocesses
    tornado.ioloop.IOLoop.current().start()

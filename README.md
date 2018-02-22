### tornado-dynamic-gallery

This repository contains a Tornado-based server that serves an image
gallery. The gallery is kept up to date using two services:

1. image-processing-service: accepts images, resizes and filters
   them, and stores them in /gallery directory
2. websockets-watcher-service: watches the /gallery directory and
   tells the client (using WebSockets) what files are in the directory

# Insight DevOps Engineering Systems Puzzle

## Approach

Having explored the different technologies, syntax, and common practices, as well as studying the code, I've noted a number of likely bugs where I think either the syntax is off, something is missing, or something is mis-labeled. To control for each potential bug, I'll be testing one fix at a time.

### Likely bugs
 -

However, to begin, I'll run the specified commands, and then try to identify and solve the bugs in an order that makes sense. The first task will be ensuring the containers are communicating properly, as this will make identifying their indvidual bugs clearer (if this doesn't work, my next move would be to try testing each in isolation).

- Initial compose:
  - http://localhost:8080 - (where the app is supposed to be hosted)'This site can't be reached'
  - http://localhost:80 - 'This page isn't working' 'localhost didn't send any data'.
  - Okay so it's likely we are not serving the correct port.
    - The `docker-compose.yml` file specifies ports `80:8080` for nginx. As the order is `host:container`, I believe this should be `8080:5001` as `8080` as `5001` is exposed by flask, which is the only other container nginx will be communicating with.
    - The `flaskapp.conf` file specifies that nginx will listen on port 80. I think this value should be 8080, as nginx should be listening for client-side input on this port.
    - logs:
      - `flaskapp_1  |  * Running on http://0.0.0.0:5000/`
        - in conflict with `Expose 5001` in Dockerfile?
    - Also of note: running `docker-compose ps` in my terminal lists the ports for each container as:
      - `5432/tcp` for postgresql
      - `5001/tcp` for flask
      - `80/tcp, 0.0.0.0:80->8080/tcp` for nginx
      - First thoughts:
        - how are postgresql and flask supposed to be communicating?
        - I think nginx should be serving at `0.0.0.0:8080`
- I will try editing `flaskapp.conf` first, as there is only one value there, so that `listen 80` is replaced with `listen 8080`
  - http://localhost:8080 - no change
  - http://localhost:80 - '502 bad gateway'
  - `docker-compose ps` - no change
- returning to original, and changing `docker-compose.yml` so that nginx ports are `"8080:8080"`:
  - `docker-compose ps` - `80/tcp, 0.0.0.0:8080->8080/tcp` for nginx
  - http://localhost:8080 - 'This page isn't working' 'localhost didn't send any data'.
  - http://localhost:80 - 'This site can't be reached'
  - logs - no change
- combing the two changes:
  - `docker-compose ps` - `80/tcp, 0.0.0.0:8080->8080/tcp` for nginx
  - http://localhost:8080 - '502 bad gateway'
  - logs - upon accessing http://localhost:8080:
    - `nginx_1     | 2019/11/25 04:26:40 [error] 6#6: *1 connect() failed (111: Connection refused) while connecting to upstream, client: 172.19.0.1, server: localhost, request: "GET / HTTP/1.1", upstream: "http://172.19.0.2:5001/", host: "localhost:8080"`
  - I think this is getting closer to a working system, as at least there is some activity happening when trying to reach `http:/localhost:8000`. Committing the changes so I know where I've left off. Three pieces of code I want to experiment with now:
    - `flaskapp.conf`: `proxy_pass http://flaskapp:5001` - should this be `5000`?
    - `Dockerfile`: `EXPOSE 5001` - should this be `5000`?
    - `docker-compose.yml`, still the nginx ports, `8080:8080` -> `8080:5001`, `8080:5000`?
    - Also of note: in the Dockerfile (which is tied to the flask container), the `FLASK_APP` environment variable is not set before running the app. Going to try adding this line first:
      `ENV FLASK_APP app.y` before exposing the port
      - no change. I'm going to remove this for now, even though I think I may need this.
    - I don't see the benefit of using port 5001 over default port 5000 for flask.
    - `flaskapp.conf`: `proxy_pass http://flaskapp:5000`
      - http:localhost/8080 displays content!
      - submitting the form leads to 'site can't be reached' - will come back to this
      - no changes to `docker-compose ps` ports.
      - Does this mean there is a connection between nginx and flask?
    - `Dockerfile`: `EXPOSE 5001`
      - changes nothing by itself, or combined with above change.
    - `docker-compose.yml` ports `8080:5001`
      - site no longer displaying content
      - `docker-compose ps` - `80/tcp, 0.0.0.0:5001->8080/tcp` for nginx
    - `docker-compose.yml` ports `8080:5000`
      - site no longer displaying content
      - `docker-compose ps` - `80/tcp, 0.0.0.0:5000->8080/tcp` for nginx
    - committing only `flaskapp.conf`: `proxy_pass http://flaskapp:5000` and moving on for now

# Insight DevOps Engineering Systems Puzzle

## Approach

Having explored the different technologies, syntax, and common practices, as well as studying the code, I've noted a number of likely bugs where I think either the syntax is off, something is missing, or something is mis-labeled. To control for each potential bug, I'll be testing one fix at a time.

### Likely bugs
A list of odd syntax, things that look mislabeled, and things I think might be missing
  - `Dockerfile` needs to declare flask_app environment variable: `ENV FLASK_APP app.py` before running `app.py`
  - `docker_compose.yml`
    - nginx ports
    - nginx environment variables missing
    - volumes for database and nginx
  - `database.py` - `create_engine(postgres...)` should be `create_engine(postgresql...)`
  - `models.py` - `Items` class needs `__init__`
  - `flaskapp.conf` listen port

### Moving through app

However, to begin, I'll run the specified commands, and then try to identify and solve the bugs in an order that makes sense. The first task will be ensuring the containers are communicating properly, as this will make identifying their individual bugs clearer (if this doesn't work, my next move would be to try testing each in isolation).

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
  - connecting database and flask
    - logs: `db_1        | LOG:  database system is ready to accept connections`
    - default port for postgresql 5432
    - from notes on likely bugs from my first pass:
      - `database.py` - `create_engine('postgres://%s:%s@%s:%s/%s' % (user, pwd, host, port, db))`
      - values look correct
      - syntax: `postgresql` insteadof `postgres`
        - no change in logs, content display, or ports
        - going to sideline issue for now, no changes saved
  - the post request not going through : logs showing
    `flaskapp_1  | 172.19.0.3 - - [25/Nov/2019 06:24:26] "POST / HTTP/1.0" 302 -
nginx_1     | 172.19.0.1 - - [25/Nov/2019:06:24:26 +0000] "POST / HTTP/1.1" 302 223 "http://localhost:8080/" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36" "-"`
    - likely an issue with routing, or rendering templates
    - from `app.py`, when creating a new Item, runs into one of my likely bugs, the `Items` class not having an `__init__` function. Going to see if this changes anything
      - no changes, commenting out these additions for now
    -  notes:
      - logs not showing get request to '/success' after submission of form, likely an error before the redirect
      - connecting to `localhost:8080/success` directly in browser displays content
      - issue not (at least not only) with creating new Item, must be with `db_session.add(item)` or `db_session.commit()`
      - after much finagling with ports, turned back to the '/success' page to confirm Items were being saved. Was able to confirm using some print statements in the `add_item()`, and altered the `success()` function to display these correctly.

  So, at this point, we have the "/" page displaying content, the form accepting content and saving it in our db, and this is persisting through the volumes, as the same data appears after stopping and restarting the app, and a '/success' page that displays the items. What isn't working is the transition from the '/' page to the '/success' page. Instead, the address routed to is "http://localhost%2Clocalhost:8080/success".

### Final thoughts.

I tried to dig in to how flask redirect and url_for work, but that only seemed to make me less sure this was an `app.py` or templates issue. I'm sure I'm missing something here. It could be a miscommunication between nginx and flask that's causing the issue. 

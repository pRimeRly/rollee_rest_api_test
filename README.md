## How to build your image

```
docker build -t DOCKER-IMAGE-NAME .
```
## How to run the Dockerfile locally

```
docker run -dp 5005:5000 -w /app -v "%cd%:/app" DOCKER-IMAGE-NAME
```

The API endpoints are accessible at "http://localhost:5005/"
To authenticate a user and retrieve an access token, send a POST request to /auth with the following JSON payload:

payload:
```
{
  "username": "your-username",
  "password": "your-password"
}
```
To retrieve user data, send a POST request to /pull with the access token included in the request headers

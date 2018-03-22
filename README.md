# MMSy

Goal: modular front-end for a simple ML-based photo-style transfer app. A focus
will be on simplicity and customizability.

This is essentially a very simple queueing system that can support a one-step
waiver workflow.

This front-end will work with any backend that supports the very simple API
described below. This application will first ask users to agree to terms and
conditions as well as a privacy policy and any additional terms (configurable)
before processing any requests.

## Requires
- Python 3.6
  - Flask
- MongoDB
- Google Cloud Storage (account and API key) for photo storage
- Twilio (account and API key) for SMS and MMS
- compatible backend API (see details below)

### Backend API
| Route                                                          | Method | Description                                                                                  | Response                                                                                                |
| -----                                                          | ------ | -----------                                                                                  | --------                                                                                                |
| `\convert?image_url=<image to convert>&style=<style to apply>` | `GET`  | Apply specified style to input image, if `style` is omitted, a default style will be applied | `{style, converted_image_url, height, width, size_in_bytes}`                                            |
| `\styles`                                                      | `GET`  | Get a list of available styles for conversion                                                | `{styles: [{name, example: {input_image_url, output_image_url}}], default_style: <default style name>}` |

#### Error codes and rate limiting
Backends that are unresponsive (`4XX` or `5XX` errors) or timeout
will trigger an exponential backoff (and eventually resulting in a `503` from
MMSy). MMSy will respect the `Retry-After` header on `429` and `503` errors
returned from the backend.

## Configure
| Env var           | Default                | Description                                |
| -------           | -------                | -----------                                |
| `MONGO_URL`       | `mongodb://localhost/` | Connection string for the MongoDB instance |
| `UNIQUE_APP_ID`   | `MMSy`                 | Unique id for each deployment              |
| `GCLOUD_API_KEY`  |                        | API key for Google Cloud Storage           |
| `TWILIO_API_KEY`  |                        | API key for Twilio                         |
| `BACKEND_API_URL` |                        | URL where a compatible API is available    |

A short (text message length) statement should be put into `user_agreement.txt`
at the project root (see `./user_agreement.txt.example`). This is the message
that will be sent to first-time users of the service and requires that they
respond with `YES` in order to proceed.

## Start the app

Install `pipenv` (https://docs.pipenv.org/)
See [Contributing](#contributing) for more information.

```
pipenv install
FLASK_APP=server.py flask run
```

## Contributing
- Pipenv

**TODO**:
- Deploy Flask behind a production-ready web server (see https://vsupalov.com/flask-web-server-in-production/ and http://flask.pocoo.org/docs/0.12/deploying/)

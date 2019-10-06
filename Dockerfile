FROM python

WORKDIR /app

ENV PORT=5000
ARG PIPENV_SYSTEM=1
ARG PIPENV_QUIET=1
ARG EXTRA_PIP_MODULES=""

RUN pip install pipenv gunicorn fs-s3fs psycopg2-binary -q

ADD Pipfile* ./
RUN pipenv install --deploy

ADD . /app
CMD [ "gunicorn", "valhalla:create_app()", "-c", "python:gunicornconfig" ]

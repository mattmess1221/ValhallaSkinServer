FROM python

ADD . /app
WORKDIR /app

ENV PORT=5000
ENV PIPENV_SYSTEM=1
ENV PIPENV_QUIET=1
ENV EXTRA_PIP_MODULES=""

RUN pip install pipenv gunicorn $EXTRA_PIP_MODULES -q
RUN pipenv install --deploy

ENTRYPOINT [ "gunicorn", "valhalla:create_app()", "-c", "python:gunicornconfig" ]
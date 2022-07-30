#!/usr/bin/env bash
export DEBUG=1 ENV=dev

uvicorn valhalla:app --reload

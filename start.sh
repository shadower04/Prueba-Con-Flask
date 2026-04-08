#!/usr/bin/env bash
gunicorn gestor.wsgi:application
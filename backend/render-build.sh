#!/bin/bash

# Instalar Java para Pellet
apt-get update
apt-get install -y default-jre

# Instalar dependencias Python
pip install -r requirements.txt

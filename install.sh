#!/bin/bash

# Frissítjük a rendszert
sudo apt update -y
sudo apt upgrade -y

# Telepítjük a Node.js-t
sudo apt install nodejs -y

# Telepítjük az NPM-t (Node Package Manager)
sudo apt install npm -y

# Telepítjük a Discord.js csomagot
npm install discord.js@13

# Telepítjük a szükséges kriptográfiai csomagokat
npm install tweetnacl

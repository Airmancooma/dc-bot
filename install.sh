#!/bin/bash

# Frissítjük a rendszert
sudo apt update -y
sudo apt upgrade -y

# Telepítjük a Node.js-t
sudo apt install nodejs -y

# Telepítjük az NPM-t (Node Package Manager)
sudo apt install npm -y

sudo apt install ffmpeg


# Telepítjük a csomagokat
npm install discord.js
npm install @discordjs/voice
npm install yt-search
npm install ytdl-core
